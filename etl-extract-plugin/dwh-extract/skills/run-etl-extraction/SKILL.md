---
name: run-etl-extraction
description: Run and interpret the data-warehouse extraction pipeline - extract a configured source into the landing zone, apply business rules, and reconcile the landed data. Use when someone wants to pull / extract / ingest a source, inspect a landing zone, or read a reconciliation report.
---

# Run an ETL extraction

CLI entry point (use `python3` if `python` is missing):

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/etl_cli.py" <command>
```

| Command | Purpose |
|---------|---------|
| `sources` | list configured sources (`--brief` for one line) |
| `types` | list registered source connectors |
| `rules` | list available business rules |
| `extract <name>` / `extract --all` | run the pipeline |
| `reconcile <name> [run_id]` | re-check a landed run |
| `runs [--source N] [--limit K]` | recent run log |

## Pipeline stages (`scripts/etl/pipeline.py`)

1. **Extract** — a connector in `scripts/etl/extractors/` reads the source to rows.
2. **Business rules** — `business_rules.py` transforms/validates each row; failures
   go to `rejects.csv` with a `_reject_reason`.
3. **Land** — `landing.py` writes `data.csv` to
   `landing/<source>/<YYYY-MM-DD>/<run_id>/`.
4. **Manifest** — `_manifest.json`: row counts, control totals, rules applied.
5. **Reconcile** — `reconciliation.py` compares the landed data back to the source
   and writes `_reconciliation.json`.

## Interpreting results

- `rows_extracted == rows_written + rows_rejected` must always hold.
- Reconciliation `status: FAIL` → report the failing check (expected vs actual)
  and treat it as "do not load downstream" (the CLI also exits 2).
- For a full write-up of one run, hand it to the `extraction-reviewer` agent.

If no name is given, run `sources` and ask which one.
