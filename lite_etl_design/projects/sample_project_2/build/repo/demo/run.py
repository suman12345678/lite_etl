"""End-to-end local demo runner. See DEMO.md.

    python -m demo.run                         # dataset=bad, control=pass  -> DQ quarantines, recon PASS, publish
    python -m demo.run --dataset good          # clean data, nothing quarantined
    python -m demo.run --dataset fixed         # the bad row corrected at source
    python -m demo.run --control-totals fail   # force a reconciliation FAIL -> publish blocked, exit 1
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

import duckdb
import yaml

from demo import checks
from demo.load import bronze_counts, load_fixtures_to_duckdb

REPO = Path(__file__).resolve().parents[1]
STATE = REPO / ".local_state"
DB = STATE / "demo.duckdb"
SQL = Path(__file__).resolve().parent / "sql"

# per dataset, the control total that reconciles (unless --control-totals overrides)
DEFAULT_CONTROL = {"good": "pass", "bad": "pass", "fixed": "fixed"}


def _load_config() -> dict:
    """defaults.yml <- ci.yml, deep-merged (config layering, environments-and-config.md)."""
    cfg: dict = {}
    for name in ("defaults.yml", "ci.yml"):
        layer = yaml.safe_load((REPO / "config" / name).read_text()) or {}
        _deep_merge(cfg, layer)
    return cfg


def _deep_merge(base: dict, over: dict) -> dict:
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v
    return base


def _banner(txt: str) -> None:
    print(f"\n{'=' * 4} {txt} {'=' * (72 - len(txt))}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", choices=["good", "bad", "fixed"], default="bad")
    ap.add_argument("--control-totals", choices=["pass", "fail", "fixed"], default=None)
    ap.add_argument("--date", default="2026-09-08", help="business date D")
    args = ap.parse_args(argv)

    cfg = _load_config()
    tol_pct = float(cfg["recon"]["tolerance_pct"])
    salt = "demo-salt-not-a-real-secret"
    run_id = f"demo-{uuid.uuid4().hex[:8]}"
    control_kind = args.control_totals or DEFAULT_CONTROL[args.dataset]
    control_csv = REPO / "tests" / "fixtures" / "recon" / f"control_totals_{control_kind}.csv"
    STATE.mkdir(exist_ok=True)

    print(f"business_date={args.date}  run_id={run_id}  dataset={args.dataset}  "
          f"control={control_csv.name}  recon.tolerance_pct={tol_pct}")

    # 1) LOAD -------------------------------------------------------------------
    _banner("1. LOAD  fixtures -> bronze.*")
    load_fixtures_to_duckdb(DB, args.date, run_id, dataset=args.dataset)
    for tbl, n in bronze_counts(DB).items():
        print(f"   {tbl:<28} {n:>4} rows")

    con = duckdb.connect(str(DB))

    # 2) TRANSFORM + DQ ------------------------------------------------------------
    _banner("2. TRANSFORM  bronze -> stg -> int -> dim/fct   (+ DQ quarantine)")
    con.execute((SQL / "10_staging.sql").read_text().replace("{salt}", salt))
    con.execute((SQL / "20_marts.sql").read_text().replace("{run_id}", run_id))

    rejects = con.execute(
        "select order_id, currency, net_amount, net_amount_usd, reason_code, _dq_rule from reject__fct_order order by order_id"
    ).fetchall()
    published = con.execute("select count(*) from fct_order").fetchone()[0]
    if rejects:
        print(f"   DQ rule DQ03 (`gmv >= 0 unless is_return`) quarantined {len(rejects)} row(s) -> reject__fct_order:")
        for r in rejects:
            print(f"      order {r[0]}  {r[1]} {r[2]} ({r[3]} USD)  reason={r[4]}  rule={r[5]}")
        print("   -> these rows are NOT published; fix them at source and re-run (`--dataset fixed`).")
    else:
        print("   DQ rule DQ03: 0 rows quarantined - all orders clean.")
    print(f"   fct_order rows published to the curated layer: {published}")

    # 3) RECONCILE --------------------------------------------------------------
    _banner("3. RECONCILE  (blocking gate - requirements/05)")
    results = [
        checks.row_count_identity(con),
        checks.gmv_control_total(con, control_csv, tol_pct),
        checks.order_equals_lines(con),
    ]
    for c in results:
        mark = "OK  " if c["verdict"] == "PASS" else "FAIL"
        print(f"   [{mark}] {c['name']:<20} expected={c['expected']:<10} actual={c['actual']:<10} "
              f"tol={c['tolerance']:<8} {c['detail']}")

    verdict = "PASS" if all(c["verdict"] == "PASS" for c in results) else "FAIL"
    recon_dir = STATE / "_recon" / f"dt={args.date}"
    recon_dir.mkdir(parents=True, exist_ok=True)
    report = {"business_date": args.date, "run_id": run_id, "verdict": verdict,
              "checks": results, "report_uri": str(recon_dir / "_reconciliation.json")}
    (recon_dir / "_reconciliation.json").write_text(json.dumps(report, indent=2, default=str))
    print(f"   _reconciliation.json -> {recon_dir / '_reconciliation.json'}")

    # 4) PUBLISH or BLOCK ----------------------------------------------------------
    _banner(f"4. GATE VERDICT: {verdict}")
    if verdict != "PASS":
        print("   PUBLISH BLOCKED - gold not updated, no _SUCCESS, watermark unchanged. Exit 1.")
        con.close()
        return 1

    con.execute("create schema if not exists gold")
    con.execute("create or replace table gold.fct_order as select * from fct_order")
    con.execute("create or replace table gold.fct_order_line as select * from fct_order_line")
    con.execute("create or replace table gold.dim_customer as select * from dim_customer")
    gold_dir = STATE / "gold"
    gold_dir.mkdir(parents=True, exist_ok=True)
    (gold_dir / f"_SUCCESS_dt={args.date}").write_text(run_id)
    gmv = con.execute("select round(sum(net_amount_usd), 2) from gold.fct_order").fetchone()[0]
    print(f"   published gold.fct_order ({published} rows, GMV {gmv} USD) + _SUCCESS marker; watermark -> {args.date}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
