"""publish.gate -- rules.yml gate + publish, the real-warehouse counterpart of
demo/rules.py + the publish step of demo/run.py. Run after `dbt build` by
orchestration/run_daily.sh (and orchestration/run_backfill.sh for a month
range): quality checks quarantine/warn/fail, then the two reconciliations
either publish or block.

    python -m publish.gate --mode publish
    python -m publish.gate --mode publish --date-range 2026-05 2026-06

Connects with extract.common.connect(schema=<marts schema for ENGINE>) so every
bare table name in rules.yml resolves without any per-engine string rewriting.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import yaml

from extract.common import connect, env

REPO = Path(__file__).resolve().parents[1]
RULES_YML = REPO / "rules.yml"
CONTROL_TOTALS_SEED = REPO / "dbt" / "seeds" / "control_totals.csv"
GOLD_DIR = Path(env("GOLD_DIR", str(REPO / "gold")))
GOLD_TABLES = ["dim_account", "dim_plan", "fct_invoice", "fct_mrr_movement"]

_MARTS_SCHEMA_DEFAULT = {"duckdb": None, "databricks": "marts", "snowflake": "MARTS"}


def _connect():
    engine = (env("ENGINE", "duckdb") or "duckdb").lower()
    schema = env("MARTS_SCHEMA", _MARTS_SCHEMA_DEFAULT.get(engine))
    return connect(engine, schema=schema), ("?" if engine == "duckdb" else "%s")


def _load_control_totals(con, placeholder: str) -> None:
    cur = con.cursor() if hasattr(con, "cursor") else con
    cur.execute("create table if not exists control_totals (metric varchar, expected_value double)")
    cur.execute("delete from control_totals")
    with open(CONTROL_TOTALS_SEED, newline="") as fh:
        for row in csv.DictReader(fh):
            cur.execute(
                f"insert into control_totals (metric, expected_value) values ({placeholder}, {placeholder})",
                (row["metric"], float(row["expected_value"])),
            )
    if hasattr(con, "commit"):
        con.commit()


def _ensure_reject_table(con, table: str) -> None:
    cur = con.cursor() if hasattr(con, "cursor") else con
    cur.execute(f"create table if not exists reject_{table} as select * from {table} where 1=0")


def run_gate(date_range: tuple[str, str] | None = None) -> dict:
    con, placeholder = _connect()
    cur = con.cursor() if hasattr(con, "cursor") else con
    report: dict = {"quality": [], "reconcile": [], "stop": False, "block": False}
    spec = yaml.safe_load(RULES_YML.read_text())

    # ---- quality ---------------------------------------------------------
    for rule in spec.get("quality", []):
        rid, table, expect, on_fail = rule["id"], rule["table"], rule["expect"], rule["on_fail"]
        cur.execute(f"select count(*) from {table} where not ({expect})")
        bad = cur.fetchone()[0]
        entry = {"id": rid, "table": table, "on_fail": on_fail, "violations": bad,
                 "action": "pass" if bad == 0 else on_fail}
        if bad:
            if on_fail == "quarantine":
                _ensure_reject_table(con, table)
                cur.execute(f"insert into reject_{table} select * from {table} where not ({expect})")
                cur.execute(f"delete from {table} where not ({expect})")
            elif on_fail == "fail":
                report["stop"] = True
        report["quality"].append(entry)
        if hasattr(con, "commit"):
            con.commit()
        if report["stop"]:
            return report

    # ---- reconcile ---------------------------------------------------------
    _load_control_totals(con, placeholder)
    for rule in spec.get("reconcile", []):
        cur.execute(rule["query"])
        actual = float(cur.fetchone()[0])
        cur.execute(rule["expect"])
        expected = float(cur.fetchone()[0])
        tol = float(rule["tolerance_pct"])
        diff_pct = abs(actual - expected) / expected * 100 if expected else (0.0 if actual == 0 else 100.0)
        ok = diff_pct <= tol
        report["reconcile"].append({
            "id": rule["id"], "actual": round(actual, 2), "expected": round(expected, 2),
            "diff_pct": round(diff_pct, 3), "tolerance_pct": tol,
            "verdict": "PASS" if ok else "FAIL", "on_fail": rule["on_fail"],
        })
        if not ok and rule["on_fail"] == "block":
            report["block"] = True

    con.close()
    return report


def publish(date_range: tuple[str, str] | None = None) -> int:
    report = run_gate(date_range)
    for q in report["quality"]:
        print(f"quality:{q['id']:<24} action={q['action']:<10} violations={q['violations']}")
    if report["stop"]:
        print("A `fail` rule tripped -> run stopped, nothing published.")
        return 1
    for r in report["reconcile"]:
        print(f"reconcile:{r['id']:<24} verdict={r['verdict']} diff={r['diff_pct']}% "
              f"(tolerance {r['tolerance_pct']}%)")
    if report["block"]:
        print("PUBLISH BLOCKED -> gold/ not written, watermark unchanged.")
        return 1

    con, placeholder = _connect()
    cur = con.cursor() if hasattr(con, "cursor") else con
    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    for table in GOLD_TABLES:
        where = ""
        params: tuple = ()
        if date_range and table == "fct_invoice":
            where = f" where invoice_month >= {placeholder} and invoice_month <= {placeholder}"
            params = date_range
        cur.execute(f"select * from {table}{where}", params) if params else cur.execute(f"select * from {table}")
        rows = cur.fetchall()
        header = [d[0] for d in cur.description]
        with (GOLD_DIR / f"{table}.csv").open("w", encoding="utf-8") as fh:
            fh.write(",".join(header) + "\n")
            for row in rows:
                fh.write(",".join("" if v is None else str(v) for v in row) + "\n")
    cur.execute("select max(invoice_month) from fct_invoice")
    watermark = cur.fetchone()[0]
    (GOLD_DIR / "_SUCCESS").write_text(f"month<={watermark}\n")
    con.close()
    print(f"published {GOLD_DIR}/  ->  {', '.join(GOLD_TABLES)}  (watermark: month <= {watermark})")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", choices=["publish"], default="publish")
    ap.add_argument("--date-range", nargs=2, metavar=("START_MONTH", "END_MONTH"), default=None)
    args = ap.parse_args(argv)
    date_range = tuple(args.date_range) if args.date_range else None
    return publish(date_range)


if __name__ == "__main__":
    sys.exit(main())
