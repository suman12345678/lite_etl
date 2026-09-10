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
    _rule("Synthetic sources (demo/load.py, seed=42 -> deterministic)")
    print(f"  currencies      : {', '.join(loader.KNOWN_CURRENCIES)}  (rate_to_usd in load.py)")
    print(f"  business days    : {loader.BUSINESS_DAYS[0]} .. {loader.BUSINESS_DAYS[-1]}"
          "   (Sat/Sun have NO fx row -> carry-forward)")
    print("  orders           : 30/day + 1 duplicate re-send (newer loaded_at -> deduped)")
    print("  customers        : 20; C001-C003 have @example.test emails -> dropped in staging")
    print("  --scenario fail  : + 3 'store' orders with negative totals -> quarantined")

    _rule("Finance control totals (demo/data/control_totals.csv)  -- editable, drives reconcile")
    print((loader.DATA / "control_totals.csv").read_text().rstrip())

    _rule("Rules (rules.yml)")
    print((REPO / "rules.yml").read_text().rstrip())


def show_state() -> None:
    if not DB.exists():
        print("No .local_state/ yet - run `python -m demo.run` first.")
        return
    con = sqlite3.connect(DB)

    _rule("Row counts")
    tables = [r[0] for r in con.execute(
        "select name from sqlite_master where type='table' order by name"
    )]
    for t in tables:
        n = con.execute(f"select count(*) from {t}").fetchone()[0]
        print(f"  {t:<22} {n:>5}")

    if "reject_fct_order" in tables:
        _rule("reject_fct_order  (quarantined, NOT published)")
        for r in con.execute(
            "select order_id, channel, currency, net_usd, reject_rule from reject_fct_order order by order_id"
        ):
            print(f"  {r[0]}  {r[1]:<9} {r[2]} {r[3]:>10}   rule={r[4]}")

    _rule("Per-channel net_usd  (pipeline vs the control total the last run reconciled against)")
    if "control_totals" in tables:
        control = dict(con.execute("select channel, expected_net_usd from control_totals"))
    else:
        control = loader.read_control_totals()
    for ch, exp in control.items():
        act = con.execute(
            "select coalesce(sum(net_usd),0) from fct_order where channel=?", (ch,)
        ).fetchone()[0]
        flag = "" if exp == 0 else f"  diff {abs(act-exp)/exp*100:5.2f}%"
        print(f"  {ch:<10} pipeline={act:12,.2f}   finance={exp:12,.2f}{flag}")
    con.close()

    _rule("Published artifacts (.local_state/gold/)")
    if GOLD.exists():
        for f in sorted(GOLD.iterdir()):
            print(f"  {f.name:<20} {f.stat().st_size:>7} bytes")
        succ = GOLD / "_SUCCESS"
        if succ.exists():
            print(f"  _SUCCESS contents  : {succ.read_text().strip()}")
    else:
        print("  (none - the run was BLOCKED, nothing published)")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "inputs":
        show_inputs()
    else:
        show_state()
