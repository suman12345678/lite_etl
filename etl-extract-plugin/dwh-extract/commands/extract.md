---
description: Run the ETL extraction pipeline for a configured source
argument-hint: <source-name | --all>
---

Run the extraction stage for: `$ARGUMENTS`

1. If `$ARGUMENTS` is empty, run
   `python "${CLAUDE_PLUGIN_ROOT}/scripts/etl_cli.py" sources`
   and ask the user which source to extract.
2. Otherwise run (use `python3` if `python` is missing):
   ```
   python "${CLAUDE_PLUGIN_ROOT}/scripts/etl_cli.py" extract $ARGUMENTS
   ```
3. Summarise: rows extracted / written / rejected, the landing path, and the
   reconciliation status. If reconciliation is FAIL or any rows were rejected,
   show the failing checks and the `rejects.csv` path, and recommend a next step
   (or offer to run the `extraction-reviewer` agent).

Exit code 2 from the CLI means a reconciliation check failed — treat that as
"do not load downstream".
