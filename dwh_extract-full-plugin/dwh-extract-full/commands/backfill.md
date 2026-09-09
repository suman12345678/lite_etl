---
description: Re-extract a historical window / replay a run
argument-hint: <source> --from DATE --to DATE
---

SCAFFOLD ONLY - not implemented yet.

Intended behaviour: idempotent backfill over a date range or key range

Run: `python "${CLAUDE_PLUGIN_ROOT}/scripts/etl_cli.py" backfill <source> --from DATE --to DATE`
See README.md and docs/operations-runbook.md.
