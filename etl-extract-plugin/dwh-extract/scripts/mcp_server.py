#!/usr/bin/env python3
"""stdio MCP server exposing the dwh-extract pipeline as callable tools.

Pure standard library. Tools:
  etl_list_sources  - configured sources and their rules
  etl_extract       - run the pipeline for one source (or all); returns manifest + reconciliation
  etl_reconcile     - re-run reconciliation for a source's latest run
  etl_list_runs     - recent extraction run log
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from etl import landing  # noqa: E402
from etl.config import load_config  # noqa: E402
from etl.pipeline import run_extraction  # noqa: E402
from etl.reconciliation import reconcile  # noqa: E402

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "dwh-extract", "version": "0.1.0"}

TOOLS = [
    {
        "name": "etl_list_sources",
        "description": "List configured ETL sources with their type, business rules and reconciliation settings.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "etl_extract",
        "description": "Run the extraction pipeline (extract -> rules -> land -> manifest -> reconcile) for one source, or all enabled sources. Returns the manifest and reconciliation report.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "Source name."},
                "all": {"type": "boolean", "description": "Extract every enabled source."},
            },
        },
    },
    {
        "name": "etl_reconcile",
        "description": "Re-run reconciliation for the latest run of a source.",
        "inputSchema": {
            "type": "object",
            "properties": {"source": {"type": "string"}},
            "required": ["source"],
        },
    },
    {
        "name": "etl_list_runs",
        "description": "Return the recent extraction run log.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {"type": "string"},
                "limit": {"type": "integer"},
            },
        },
    },
]


def _text(payload) -> dict:
    body = payload if isinstance(payload, str) else json.dumps(payload, indent=2, default=str)
    return {"content": [{"type": "text", "text": body}]}


def _call(name, args):
    cfg = load_config()

    if name == "etl_list_sources":
        return _text([
            {"name": s.name, "type": s.type, "enabled": s.enabled,
             "business_rules": s.business_rules, "reconciliation": s.reconciliation}
            for s in cfg.sources
        ])

    if name == "etl_extract":
        if args.get("all"):
            targets = [s for s in cfg.sources if s.enabled]
        else:
            targets = [cfg.get(args["source"])]
        return _text([
            {"source": s.name, **run_extraction(s, cfg.landing_zone)} for s in targets
        ])

    if name == "etl_reconcile":
        base = Path(cfg.landing_zone) / args["source"]
        runs = sorted(p for p in base.glob("*/run_*") if (p / "_manifest.json").exists())
        if not runs:
            return _text(f"No completed runs for '{args['source']}'.")
        run_path = runs[-1]
        manifest = json.loads((run_path / "_manifest.json").read_text(encoding="utf-8"))
        report = reconcile(cfg.get(args["source"]), manifest, run_path)
        landing.write_json(run_path, "_reconciliation.json", report)
        return _text(report)

    if name == "etl_list_runs":
        log = Path(cfg.landing_zone) / "_runs.jsonl"
        if not log.exists():
            return _text("No runs yet.")
        rows = [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines() if l.strip()]
        if args.get("source"):
            rows = [r for r in rows if r.get("source") == args["source"]]
        return _text(rows[-int(args.get("limit", 20)):])

    raise ValueError(f"Unknown tool: {name}")


def handle(msg):
    method, mid = msg.get("method"), msg.get("id")

    if method == "initialize":
        return _ok(mid, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": SERVER_INFO,
        })
    if method == "tools/list":
        return _ok(mid, {"tools": TOOLS})
    if method == "tools/call":
        params = msg.get("params") or {}
        try:
            return _ok(mid, _call(params.get("name"), params.get("arguments") or {}))
        except Exception as exc:  # noqa: BLE001 - report errors as tool results
            return _ok(mid, {"content": [{"type": "text", "text": f"ERROR: {exc}"}],
                             "isError": True})
    if method == "ping":
        return _ok(mid, {})
    if mid is None:
        return None
    return {"jsonrpc": "2.0", "id": mid,
            "error": {"code": -32601, "message": f"Method not found: {method}"}}


def _ok(mid, result):
    return {"jsonrpc": "2.0", "id": mid, "result": result}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = handle(msg)
        if resp is not None:
            sys.stdout.write(json.dumps(resp, default=str) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
