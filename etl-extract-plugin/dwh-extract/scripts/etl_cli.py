#!/usr/bin/env python3
"""dwh-extract command-line interface.

    python etl_cli.py sources [--brief]
    python etl_cli.py types
    python etl_cli.py rules
    python etl_cli.py extract <source> | --all
    python etl_cli.py reconcile <source> [run_id]
    python etl_cli.py runs [--source NAME] [--limit N]

Exit code 2 means a reconciliation check FAILED (use it to gate the warehouse load).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from etl import landing  # noqa: E402
from etl.business_rules import available as available_rules  # noqa: E402
from etl.config import default_config_path, load_config  # noqa: E402
from etl.extractors import registered_types  # noqa: E402
from etl.pipeline import run_extraction  # noqa: E402
from etl.reconciliation import reconcile  # noqa: E402


def _dump(obj) -> None:
    print(json.dumps(obj, indent=2, default=str))


def cmd_sources(args) -> int:
    try:
        cfg = load_config(args.config)
    except FileNotFoundError as exc:
        print(exc)
        return 0
    if args.brief:
        listed = ", ".join(
            f"{s.name}({s.type}{'' if s.enabled else ',disabled'})" for s in cfg.sources
        ) or "none"
        print(f"[dwh-extract] landing zone : {cfg.landing_zone}")
        print(f"[dwh-extract] sources      : {listed}")
        print("[dwh-extract] commands     : /extract  /reconcile  /etl-status")
        return 0
    _dump([
        {
            "name": s.name,
            "type": s.type,
            "enabled": s.enabled,
            "extract_mode": s.extract.get("mode", "full"),
            "business_rules": s.business_rules,
            "reconciliation": s.reconciliation,
        }
        for s in cfg.sources
    ])
    return 0


def cmd_types(args) -> int:
    _dump({"registered_source_types": registered_types()})
    return 0


def cmd_rules(args) -> int:
    _dump({"available_business_rules": available_rules()})
    return 0


def _print_run(source_name, source_type, result) -> bool:
    m, r = result["manifest"], result["reconciliation"]
    print(f"\n=== {source_name} ({source_type}) ===")
    print(f"run_id         : {m['run_id']}")
    print(f"rows extracted : {m['rows_extracted']}")
    print(f"rows written   : {m['rows_written']}")
    print(f"rows rejected  : {m['rows_rejected']}")
    print(f"landing path   : {m['landing_path']}")
    print(f"reconciliation : {r['status']}")
    for c in r["checks"]:
        flag = "PASS" if c["status"] == "PASS" else "FAIL"
        print(f"  [{flag}] {c['check']}: expected={c['expected']} "
              f"actual={c['actual']}  {c['detail']}".rstrip())
    return r["status"] == "PASS"


def cmd_extract(args) -> int:
    cfg = load_config(args.config)
    if args.all:
        targets = [s for s in cfg.sources if s.enabled]
    else:
        targets = [cfg.get(args.source)]

    if not targets:
        print("No enabled sources to extract.")
        return 0

    all_pass = True
    for src in targets:
        result = run_extraction(src, cfg.landing_zone)
        all_pass &= _print_run(src.name, src.type, result)
    return 0 if all_pass else 2


def _latest_run_dir(landing_zone, source_name, run_id=None) -> Path:
    base = Path(landing_zone) / source_name
    runs = sorted(p for p in base.glob("*/run_*") if (p / "_manifest.json").exists())
    if run_id:
        for p in runs:
            if p.name == run_id:
                return p
        raise FileNotFoundError(f"run_id '{run_id}' not found for '{source_name}'")
    if not runs:
        raise FileNotFoundError(f"No completed runs for '{source_name}' under {base}")
    return runs[-1]


def cmd_reconcile(args) -> int:
    cfg = load_config(args.config)
    src = cfg.get(args.source)
    run_path = _latest_run_dir(cfg.landing_zone, src.name, args.run_id)
    manifest = json.loads((run_path / "_manifest.json").read_text(encoding="utf-8"))
    report = reconcile(src, manifest, run_path)
    landing.write_json(run_path, "_reconciliation.json", report)
    _dump(report)
    return 0 if report["status"] == "PASS" else 2


def cmd_runs(args) -> int:
    cfg = load_config(args.config)
    log = Path(cfg.landing_zone) / "_runs.jsonl"
    if not log.exists():
        print("No runs yet.")
        return 0
    rows = [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines() if l.strip()]
    if args.source:
        rows = [r for r in rows if r.get("source") == args.source]
    for r in rows[-args.limit:]:
        print(f"{r['finished_utc']}  {r['source']:<16} {r['run_id']}  "
              f"written={r['rows_written']} rejected={r['rows_rejected']}  "
              f"recon={r['reconciliation']}")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="etl_cli", description=__doc__.splitlines()[0])
    p.add_argument("--config", help=f"sources.json path (default: {default_config_path()})")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("sources", help="list configured sources")
    sp.add_argument("--brief", action="store_true", help="one-line summary (used by the hook)")
    sp.set_defaults(func=cmd_sources)

    sub.add_parser("types", help="list registered source connectors").set_defaults(func=cmd_types)
    sub.add_parser("rules", help="list available business rules").set_defaults(func=cmd_rules)

    sp = sub.add_parser("extract", help="run the extraction pipeline")
    grp = sp.add_mutually_exclusive_group(required=True)
    grp.add_argument("source", nargs="?", help="source name")
    grp.add_argument("--all", action="store_true", help="every enabled source")
    sp.set_defaults(func=cmd_extract)

    sp = sub.add_parser("reconcile", help="re-run reconciliation for a run")
    sp.add_argument("source")
    sp.add_argument("run_id", nargs="?", help="specific run_id (default: latest)")
    sp.set_defaults(func=cmd_reconcile)

    sp = sub.add_parser("runs", help="show recent run log")
    sp.add_argument("--source")
    sp.add_argument("--limit", type=int, default=20)
    sp.set_defaults(func=cmd_runs)

    args = p.parse_args(argv)
    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())
