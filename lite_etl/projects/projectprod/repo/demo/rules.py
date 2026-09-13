"""Run repo/rules.yml against the SQLite marts.

quality   -> warn / quarantine / fail   (row-level correctness)
reconcile -> block                       (aggregates agree with finance / tie out)

Returns a dict the runner uses to decide publish vs block. The same rules.yml also
backs dbt tests (dbt/tests/) and the publish gate in prod -- one file, three
enforcement points.
"""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
RULES_YML = REPO / "rules.yml"
CONTROL_CSV = Path(__file__).resolve().parent / "data" / "control_totals.csv"


def _load_control_totals(con: sqlite3.Connection) -> None:
    """Finance's source-of-truth numbers -> a table the reconcile SQL reads."""
    con.execute("drop table if exists control_totals")
    con.execute("create table control_totals (metric text, expected_value real)")
    with open(CONTROL_CSV, newline="") as fh:
        for row in csv.DictReader(fh):
            con.execute("insert into control_totals values (?, ?)",
                        (row["metric"], float(row["expected_value"])))


def _ensure_reject_table(con: sqlite3.Connection, table: str) -> None:
    reject = f"reject_{table}"
    cols = [r[1] for r in con.execute(f"pragma table_info({table})")]
    if not cols:
        return
    if not con.execute(
        "select 1 from sqlite_master where type='table' and name=?", (reject,)
    ).fetchone():
        collist = ", ".join(cols)
        con.execute(
            f"create table {reject} as select {collist}, '' as reject_rule, "
            f"current_timestamp as rejected_at from {table} where 0"
        )


def run(db_path: Path) -> dict:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    report: dict = {"quality": [], "reconcile": [], "stop": False, "block": False}

    spec = yaml.safe_load(RULES_YML.read_text())

    # ---- quality -------------------------------------------------------------
    for rule in spec.get("quality", []):
        rid, table, expect, on_fail = (
            rule["id"], rule["table"], rule["expect"], rule["on_fail"],
        )
        bad = con.execute(f"select count(*) from {table} where not ({expect})").fetchone()[0]
        entry = {"id": rid, "table": table, "on_fail": on_fail, "violations": bad,
                 "action": "pass" if bad == 0 else on_fail}
        if bad:
            if on_fail == "quarantine":
                _ensure_reject_table(con, table)
                con.execute(
                    f"insert into reject_{table} "
                    f"select *, ?, current_timestamp from {table} where not ({expect})",
                    (rid,),
                )
                con.execute(f"delete from {table} where not ({expect})")
            elif on_fail == "fail":
                report["stop"] = True
        report["quality"].append(entry)
        if report["stop"]:
            con.commit()
            con.close()
            return report

    # ---- reconcile -------------------------------------------------------
    _load_control_totals(con)
    for rule in spec.get("reconcile", []):
        actual = float(con.execute(rule["query"]).fetchone()[0])
        expected = float(con.execute(rule["expect"]).fetchone()[0])
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

    con.commit()
    con.close()
    return report
