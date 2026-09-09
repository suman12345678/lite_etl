---
description: Re-run reconciliation for the latest (or a given) extraction run
argument-hint: <source-name> [run_id]
---

Run (use `python3` if `python` is missing):

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/etl_cli.py" reconcile $ARGUMENTS
```

Then present every check as PASS/FAIL with expected vs actual, and give an
overall verdict. If anything failed, explain the most likely cause and what to
do about it.
