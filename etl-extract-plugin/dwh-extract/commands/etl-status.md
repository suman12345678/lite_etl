---
description: Show configured sources, registered connectors, and recent extraction runs
---

Run these and present the results as a short dashboard (use `python3` if needed):

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/etl_cli.py" sources
python "${CLAUDE_PLUGIN_ROOT}/scripts/etl_cli.py" types
python "${CLAUDE_PLUGIN_ROOT}/scripts/etl_cli.py" rules
python "${CLAUDE_PLUGIN_ROOT}/scripts/etl_cli.py" runs --limit 10
```

Group the output as: **Sources**, **Connectors available**, **Business rules
available**, **Recent runs** (note any with `recon=FAIL`).
