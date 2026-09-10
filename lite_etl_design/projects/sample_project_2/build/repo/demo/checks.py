"""The three reconciliation checks the demo runs, matching the shape of
`recon/gate.py::CheckResult` (name / applies_to / expected / actual / delta /
tolerance / verdict / detail). The real project runs the full 8 from
requirements/05 as dbt `tag:recon` tests + a Python manifest compare.
"""

from __future__ import annotations

import csv
from pathlib import Path


def _result(name, applies_to, expected, actual, tolerance, verdict, detail=""):
    return {
        "name": name,
        "applies_to": applies_to,
        "expected": round(float(expected), 4),
        "actual": round(float(actual), 4),
        "delta": round(float(actual) - float(expected), 4),
        "tolerance": tolerance,
        "verdict": verdict,
        "detail": detail,
    }


def row_count_identity(con) -> dict:
    """R1: landed orders == published + quarantined + soft-deleted."""
    landed = con.execute("select count(*) from bronze.oltp__orders").fetchone()[0]
    deleted = con.execute("select count(*) from bronze.oltp__orders where is_deleted").fetchone()[0]
    rejected = con.execute("select count(*) from reject__fct_order").fetchone()[0]
    published = con.execute("select count(*) from fct_order").fetchone()[0]
    accounted = published + rejected + deleted
    verdict = "PASS" if accounted == landed else "FAIL"
    return _result(
        "row_count_identity", "oltp.orders", landed, accounted, "exact", verdict,
        f"landed={landed} published={published} quarantined={rejected} soft_deleted={deleted}",
    )


def gmv_control_total(con, control_csv: str | Path, tolerance_pct: float) -> dict:
    """R2: SUM(net_amount_usd) per channel in fct_order vs the source-of-truth control total."""
    with open(control_csv, newline="") as fh:
        control = {r["channel"]: float(r["expected_gmv_usd"]) for r in csv.DictReader(fh)}
    channel = "direct"
    expected = control[channel]
    actual = con.execute(
        "select coalesce(sum(net_amount_usd), 0) from fct_order where channel = ?", [channel]
    ).fetchone()[0]
    delta_pct = abs(actual - expected) / expected * 100 if expected else 0.0
    verdict = "PASS" if delta_pct <= tolerance_pct else "FAIL"
    return _result(
        "gmv_control_total", f"gold.fct_order/{channel}", expected, actual,
        f"+/-{tolerance_pct}%", verdict, f"delta {delta_pct:.3f}% of control (source: {Path(control_csv).name})",
    )


def order_equals_lines(con, tolerance: float = 0.01) -> dict:
    """R4: fct_order.net_amount_usd == SUM(fct_order_line.net_amount_usd) per order."""
    breaches = con.execute(
        """
        select o.order_id, o.net_amount_usd,
               coalesce(sum(l.net_amount_usd), 0) as line_sum
        from fct_order o
        left join fct_order_line l on l.order_id = o.order_id
        group by o.order_id, o.net_amount_usd
        having abs(o.net_amount_usd - coalesce(sum(l.net_amount_usd), 0)) > ?
        """,
        [tolerance],
    ).fetchall()
    verdict = "PASS" if not breaches else "FAIL"
    detail = "all orders balance" if not breaches else f"{len(breaches)} order(s) off: {breaches}"
    return _result("order_equals_lines", "gold.fct_order vs fct_order_line", 0, len(breaches), f"+/-{tolerance}", verdict, detail)
