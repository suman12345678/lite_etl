"""Inspect the pipeline's inputs and outputs around a run.

    python -m demo.peek inputs   # BEFORE: the source-data recipe, rules.yml, finance totals
    python -m demo.peek          # AFTER:  what the last run built in .local_state/
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

from demo import load as loader

REPO = Path(__file__).resolve().parents[1]
STATE = REPO / ".local_state"
DB = STATE / "demo.sqlite"
GOLD = STATE / "gold"


def _rule(txt: str) -> None:
    print(f"\n{txt}\n{'-' * len(txt)}")


def show_inputs() -> None:
    _rule("Synthetic sources (demo/load.py - no random, fully deterministic)")
    print(f"  months           : {', '.join(loader.MONTHS)}   (current = {loader.CURRENT_MONTH})")
    print(f"  plans            : {', '.join(f'{k} ${int(v)}' for k, v in loader.PLAN_PRICE.items())}")
    print(f"  accounts         : {len(loader.ACCOUNT_GEO)} + 1 merged (A013 -> A007)")
    print(f"  subscriptions    : {len(loader.SUBSCRIPTIONS)}  (planted: 1 upgrade, 1 downgrade, "
          "1 churn, 2 new, 1 reactivation)")
    print("  fx_rates         : USD/EUR/GBP per currency per day; GBP missing for the current "
          "month -> day-grain carry forward")
    print("  invoices         : 1 paid per active sub per month + 1 webhook retry (deduped)")
    print("  --scenario fail  : + negative-amount / bad-status / unknown-plan invoices;")
    print("                     churn movements dropped -> MRR identity breaks")

    _rule("Finance control totals (demo/data/control_totals.csv)  -- editable, drives reconcile 1")
    print((loader.DATA / "control_totals.csv").read_text().rstrip())

    _rule("Rules (rules.yml)")
    print((REPO / "rules.yml").read_text().rstrip())


def show_state() -> None:
    if not DB.exists():
        print("No .local_state/ yet - run `python -m demo.run` first.")
        return
    con = sqlite3.connect(DB)
    tables = [r[0] for r in con.execute(
        "select name from sqlite_master where type='table' order by name"
    )]

    _rule("Row counts")
    for t in tables:
        n = con.execute(f"select count(*) from {t}").fetchone()[0]
        print(f"  {t:<26} {n:>5}")

    if "reject_fct_invoice" in tables:
        _rule("reject_fct_invoice  (quarantined, NOT published)")
        for r in con.execute(
            "select invoice_id, account_id, plan_code, status, amount_usd, reject_rule "
            "from reject_fct_invoice order by invoice_id"
        ):
            print(f"  {r[0]}  {r[1]:<5} {r[2]:<11} {r[3]:<6} {r[4]:>10}   rule={r[5]}")

    _rule("MRR by month  (from subscriptions x prorated plan price)")
    for m, tot in con.execute(
        "select month, round(sum(mrr_usd),2) from int_mrr_by_month group by month order by month"
    ):
        print(f"  {m}   {tot:12,.2f}")

    _rule("Current-month movements (fct_mrr_movement)")
    for mt, cnt, amt in con.execute(
        "select movement_type, count(*), round(sum(movement_amount),2) from fct_mrr_movement "
        "where month = (select max(month) from fct_mrr_movement) group by movement_type order by movement_type"
    ):
        print(f"  {mt:<13} n={cnt}   sum={amt:>10,.2f}")

    _rule("Reconciliations")
    rev_actual = con.execute(
        "select coalesce(sum(recognized_revenue_usd),0) from fct_invoice "
        "where invoice_month = (select max(invoice_month) from fct_invoice)"
    ).fetchone()[0]
    ctl = loader.read_control_totals().get("recognized_revenue_usd_current_month", 0.0)
    print(f"  revenue_vs_finance_gl : pipeline={rev_actual:12,.2f}   finance={ctl:12,.2f}")
    rec = con.execute("select opening_mrr, closing_mrr, movement_sum from mrr_recon").fetchone()
    ident = rec[0] + rec[2]
    print(f"  mrr_movement_identity : closing ={rec[1]:12,.2f}   opening+moves={ident:12,.2f}"
          f"   (opening {rec[0]:,.2f} + moves {rec[2]:,.2f})")

    _rule("Published artifacts (.local_state/gold/)")
    if GOLD.exists():
        for f in sorted(GOLD.iterdir()):
            print(f"  {f.name:<26} {f.stat().st_size:>7} bytes")
        succ = GOLD / "_SUCCESS"
        if succ.exists():
            print(f"  _SUCCESS contents         : {succ.read_text().strip()}")
    else:
        print("  (none - the run was BLOCKED, nothing published)")
    con.close()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "inputs":
        show_inputs()
    else:
        show_state()
