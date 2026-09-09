#!/usr/bin/env python3
"""SessionStart hook - prints a one-line orientation for the dwh-extract-full plugin.

SCAFFOLD: later this will summarise configured sources, the active environment,
the landing root, and any unprocessed files in requirements/inbox/.
"""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
inbox = root / "requirements" / "inbox"
pending = [p.name for p in inbox.glob("*") if p.is_file() and p.name != ".gitkeep"] if inbox.exists() else []

print(
    "[dwh-extract-full | SCAFFOLD] commands: /extract /extract-all /reconcile "
    "/validate-config /dq-report /landing-status /quarantine-review /backfill "
    "/register-source /ingest-requirements"
)
if pending:
    print(f"[dwh-extract-full] requirements/inbox has {len(pending)} unprocessed file(s): {', '.join(pending)}")
