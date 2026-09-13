"""projectprod end-to-end, local, zero-cloud.  See ../README.md.

    python -m demo.run                 # clean run  -> all checks pass -> publish gold/
    python -m demo.run --scenario fail # bad data   -> quarantine + MRR identity BLOCK -> exit 1

Flow: load synthetic sources (stand-in for extract/billing, extract/crm, extract/ref)
-> staging -> intermediate -> marts -> rules.yml gate -> publish or block.
Engine here is stdlib sqlite3; in prod the same dbt SQL + rules.yml run on
DuckDB / Databricks / Snowflake (chosen by the Terraform `engine` variable).
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sqlite3
import sys
from pathlib import Path

from demo import load as loader
from demo import rules as rules_engine

REPO = Path(__file__).resolve().parents[1]
STATE = REPO / ".local_state"
DB = STATE / "demo.sqlite"
GOLD = STATE / "gold"
SQL_DIR = Path(__file__).resolve().parent / "sql"

GOLD_TABLES = ["dim_account", "dim_plan", "fct_invoice", "fct_mrr_movement"]


def _banner(txt: str) -> None:
    print(f"\n{'=' * 3} {txt} {'=' * max(3, 70 - len(txt))}")


def _apply_sql(con: sqlite3.Connection, path: Path) -> None:
    con.create_function(
        "sha256", 1, lambda s: hashlib.sha256(str(s).encode()).hexdigest(), deterministic=True
    )
    con.executescript(path.read_text())
    con.commit()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--scenario", choices=["clean", "fail"], default="clean")
    args = ap.parse_args(argv)
    scen = args.scenario
    if STATE.exists():
        shutil.rmtree(STATE)
    STATE.mkdir(parents=True)

    print(f"scenario={scen}   engine=sqlite (local demo)   rules={REPO / 'rules.yml'}")

    # 1. LOAD ---------------------------------------------------------------------
    _banner("1. LOAD   extract/billing + extract/crm + extract/ref (synthetic here) -> raw.*")
    loader.load(DB, scenario=scen)
    for tbl, n in loader.raw_counts(DB).items():
        print(f"    {tbl:<26} {n:>4} rows")

    # 2. TRANSFORM --------------------------------------------------------------
    _banner("2. TRANSFORM   raw -> staging -> intermediate -> marts   (dbt SQL, run here on sqlite)")
    con = sqlite3.connect(DB)
    _apply_sql(con, SQL_DIR / "10_staging.sql")
    _apply_sql(con, SQL_DIR / "20_marts.sql")

    if scen == "fail":
        # simulate a churn-detection bug: churn movements never get written
        con.execute("delete from fct_mrr_movement where movement_type = 'churn'")
        con.commit()
        print("    [scenario=fail] churn movements dropped (simulated ETL bug)")

    for tbl in ("stg_billing_invoices", "stg_crm_accounts", "stg_billing_subscriptions",
                "int_mrr_by_month", "dim_account", "dim_plan", "fct_invoice", "fct_mrr_movement"):
        n = con.execute(f"select count(*) from {tbl}").fetchone()[0]
        print(f"    {tbl:<26} {n:>4} rows")
    deduped = con.execute("select count(*) from raw_billing_invoices").fetchone()[0] - con.execute(
        "select count(*) from stg_billing_invoices"
    ).fetchone()[0]
    merged = con.execute(
        "select count(*) from raw_crm_accounts where merged_into is not null"
    ).fetchone()[0]
    print(f"    (deduped {deduped} webhook invoice; resolved {merged} merged account)")
    con.close()

    # 3. RULES GATE ------------------------------------------------------------
    _banner("3. RULES GATE   repo/rules.yml")
    report = rules_engine.run(DB)

    for q in report["quality"]:
        mark = "ok  " if q["action"] == "pass" else q["action"].upper()
        print(f"    [{mark:^10}] quality:{q['id']:<24} violations={q['violations']}")
    if report["stop"]:
        print("\n    A `fail` rule tripped -> run stopped, nothing published. Exit 1.")
        return 1

    con = sqlite3.connect(DB)
    if con.execute(
        "select count(*) from sqlite_master where type='table' and name='reject_fct_invoice'"
    ).fetchone()[0]:
        rows = con.execute(
            "select invoice_id, account_id, plan_code, status, amount_usd, reject_rule "
            "from reject_fct_invoice order by invoice_id"
        ).fetchall()
        print(f"\n    reject_fct_invoice  ({len(rows)} row(s) quarantined, NOT published):")
        for r in rows:
            print(f"        {r[0]}  {r[1]:<5} {r[2]:<11} {r[3]:<6} {r[4]:>10}   rule={r[5]}")
    con.close()

    for r in report["reconcile"]:
        mark = "ok  " if r["verdict"] == "PASS" else "BLOCK"
        print(
            f"\n    [{mark:^10}] reconcile:{r['id']}"
            f"\n                 actual   = {r['actual']:>12,.2f}"
            f"\n                 expected = {r['expected']:>12,.2f}"
            f"\n                 diff     = {r['diff_pct']}%   (tolerance {r['tolerance_pct']}%)"
        )

    # 4. PUBLISH or BLOCK ------------------------------------------------------
    _banner("4. VERDICT")
    if report["block"]:
        print("    PUBLISH BLOCKED -> gold/ not written, no _SUCCESS, watermark unchanged. Exit 1.")
        return 1

    con = sqlite3.connect(DB)
    GOLD.mkdir(parents=True, exist_ok=True)
    for tbl in GOLD_TABLES:
        cur = con.execute(f"select * from {tbl}")
        header = [d[0] for d in cur.description]
        rows = cur.fetchall()
        with (GOLD / f"{tbl}.csv").open("w", encoding="utf-8") as fh:
            fh.write(",".join(header) + "\n")
            for row in rows:
                fh.write(",".join("" if v is None else str(v) for v in row) + "\n")
    watermark = con.execute("select max(invoice_month) from fct_invoice").fetchone()[0]
    revenue = con.execute(
        "select round(sum(recognized_revenue_usd), 2) from fct_invoice where invoice_month = ?",
        (watermark,),
    ).fetchone()[0]
    closing_mrr = con.execute("select closing_mrr from mrr_recon").fetchone()[0]
    (GOLD / "_SUCCESS").write_text(f"month<={watermark}\n")
    con.close()
    print(f"    published gold/  ->  {', '.join(GOLD_TABLES)}")
    print(f"    {watermark} recognized revenue {revenue:,.2f} USD   closing MRR {closing_mrr:,.2f} USD")
    print(f"    wrote {GOLD / '_SUCCESS'}   (watermark: month <= {watermark})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
