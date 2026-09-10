"""retail_demo end-to-end, local, zero-install.  See DEMO.md.

    python -m demo.run                 # clean run  -> all checks pass -> publish gold/
    python -m demo.run --scenario fail # bad data   -> quarantine + reconcile BLOCK -> exit 1

Flow:  load synthetic sources -> staging -> marts -> rules.yml gate -> publish or block.
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

# in the 'fail' scenario, pretend finance's web total is 12% off the pipeline's
WEB_CONTROL_MULTIPLIER = {"clean": 1.0, "fail": 1.12}


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

    # 1. LOAD -----------------------------------------------------------------
    _banner("1. LOAD   synthetic sources -> raw.*")
    loader.load(DB, scenario=scen)
    for tbl, n in loader.raw_counts(DB).items():
        print(f"    {tbl:<16} {n:>4} rows")

    # 2. TRANSFORM ----------------------------------------------------------------
    _banner("2. TRANSFORM   raw -> staging -> marts   (dbt SQL, run here on sqlite)")
    con = sqlite3.connect(DB)
    _apply_sql(con, SQL_DIR / "10_staging.sql")
    _apply_sql(con, SQL_DIR / "20_marts.sql")
    for tbl in ("stg_orders", "stg_customers", "stg_fx_rates", "dim_customer", "fct_order"):
        n = con.execute(f"select count(*) from {tbl}").fetchone()[0]
        print(f"    {tbl:<16} {n:>4} rows")
    dropped = con.execute("select count(*) from raw_customers").fetchone()[0] - con.execute(
        "select count(*) from stg_customers"
    ).fetchone()[0]
    deduped = con.execute("select count(*) from raw_orders").fetchone()[0] - con.execute(
        "select count(*) from stg_orders"
    ).fetchone()[0]
    print(f"    (dropped {dropped} test-email customers; deduped {deduped} resent order)")
    con.close()

    # 3. RULES GATE ----------------------------------------------------------------
    _banner("3. RULES GATE   repo/rules.yml")
    report = rules_engine.run(DB, web_control_multiplier=WEB_CONTROL_MULTIPLIER[scen])

    for q in report["quality"]:
        mark = "ok  " if q["action"] == "pass" else q["action"].upper()
        print(f"    [{mark:^10}] quality:{q['id']:<24} violations={q['violations']}")
    if report["stop"]:
        print("\n    A `fail` rule tripped -> run stopped, nothing published. Exit 1.")
        return 1

    con = sqlite3.connect(DB)
    rej = con.execute(
        "select count(*) from sqlite_master where type='table' and name='reject_fct_order'"
    ).fetchone()[0]
    if rej:
        rows = con.execute(
            "select order_id, channel, currency, net_usd, reject_rule from reject_fct_order "
            "order by order_id"
        ).fetchall()
        print(f"\n    reject_fct_order  ({len(rows)} row(s) quarantined, NOT published):")
        for r in rows:
            print(f"        {r[0]}  {r[1]:<9} {r[2]} {r[3]:>10}   rule={r[4]}")
    con.close()

    for r in report["reconcile"]:
        mark = "ok  " if r["verdict"] == "PASS" else "BLOCK"
        print(
            f"\n    [{mark:^10}] reconcile:{r['id']}"
            f"\n                 pipeline = {r['actual']:>12,.2f} USD"
            f"\n                 finance  = {r['expected']:>12,.2f} USD"
            f"\n                 diff     = {r['diff_pct']}%   (tolerance {r['tolerance_pct']}%)"
        )

    # 4. PUBLISH or BLOCK --------------------------------------------------------
    _banner("4. VERDICT")
    if report["block"]:
        print("    PUBLISH BLOCKED -> gold/ not written, no _SUCCESS, watermark unchanged. Exit 1.")
        return 1

    con = sqlite3.connect(DB)
    GOLD.mkdir(parents=True, exist_ok=True)
    for tbl in ("dim_customer", "fct_order"):
        rows = con.execute(f"select * from {tbl}").fetchall()
        header = [d[0] for d in con.execute(f"select * from {tbl} limit 0").description]
        out = GOLD / f"{tbl}.csv"
        with out.open("w", encoding="utf-8") as fh:
            fh.write(",".join(header) + "\n")
            for row in rows:
                fh.write(",".join("" if v is None else str(v) for v in row) + "\n")
    gmv = con.execute("select round(sum(net_usd), 2) from fct_order").fetchone()[0]
    published = con.execute("select count(*) from fct_order").fetchone()[0]
    watermark = con.execute("select max(order_date) from fct_order").fetchone()[0]
    (GOLD / "_SUCCESS").write_text(f"order_date<={watermark}\n")
    con.close()
    print(f"    published gold/  ->  fct_order {published} rows, total {gmv:,.2f} USD")
    print(f"    wrote {GOLD / '_SUCCESS'}   (watermark: order_date <= {watermark})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
