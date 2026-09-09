#!/usr/bin/env python3
"""stdio MCP server for dwh-extract-full.

SCAFFOLD: a valid, minimal MCP server so the plugin loads cleanly. It advertises
zero tools today. As the engine is built, expose: etl_extract, etl_reconcile,
etl_dq_report, etl_landing_status, etl_validate_config, etl_ingest_requirements.
"""
import json
import sys

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "dwh-extract-full", "version": "0.0.1"}
TOOLS: list = []  # TODO: populate as engine features land


def handle(msg):
    method, mid = msg.get("method"), msg.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": mid, "result": {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": SERVER_INFO,
        }}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}}
    if method == "ping":
        return {"jsonrpc": "2.0", "id": mid, "result": {}}
    if mid is None:
        return None
    return {"jsonrpc": "2.0", "id": mid,
            "error": {"code": -32601, "message": f"Method not found: {method}"}}


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
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
