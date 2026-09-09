#!/usr/bin/env python3
"""dwh-extract-full CLI - SCAFFOLD.

Every subcommand is a stub today. The parser, subcommands, and exit-code contract
are wired so the surface is visible; each command's logic is filled in later.

Exit codes (target):
  0  success / all reconciliation checks PASS
  2  a reconciliation or data-quality gate FAILED
  3  configuration invalid
  1  unexpected error
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PLUGIN_ROOT / "config"


def _todo(name: str) -> int:
    print(f"[dwh-extract-full] '{name}' is a SCAFFOLD - not implemented yet.")
    print("See README.md and docs/ for the intended behaviour.")
    return 0


def cmd_validate_config(args) -> int:
    if not CONFIG_DIR.exists():
        print(f"config dir missing: {CONFIG_DIR}")
        return 3
    files = sorted(p.relative_to(PLUGIN_ROOT).as_posix()
                   for p in CONFIG_DIR.rglob("*")
                   if p.is_file() and p.suffix in {".yaml", ".yml"})
    print(f"[dwh-extract-full] discovered {len(files)} config file(s):")
    for f in files:
        print(f"  {f}")
    print("\nValidation logic is a SCAFFOLD - no schema checks run yet.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="etl_cli", description="dwh-extract-full CLI (scaffold)")
    p.add_argument("--env", default="dev", help="environment overlay (dev/test/prod)")
    sub = p.add_subparsers(dest="cmd", required=True)

    specs = {
        "extract": "run the pipeline for one source (positional: source; or --all)",
        "reconcile": "re-run reconciliation for a source's latest/given run",
        "dq-report": "show the data-quality result for a run",
        "landing-status": "show landing-zone contents and recent runs",
        "quarantine": "inspect quarantined / rejected records",
        "backfill": "re-extract a historical window / replay a run",
        "register-source": "scaffold config for a new source",
        "ingest-requirements": "turn requirements/inbox files into draft config",
        "runs": "show the run log",
    }
    for name, help_text in specs.items():
        sp = sub.add_parser(name, help=help_text)
        sp.add_argument("args", nargs="*", help="(scaffold) free-form args")
        sp.add_argument("--all", action="store_true")
        sp.set_defaults(func=lambda a, n=name: _todo(n))

    sp = sub.add_parser("validate-config", help="list + (later) validate all config")
    sp.set_defaults(func=cmd_validate_config)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())
