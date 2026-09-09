---
name: add-data-source
description: Add a data source or a whole new connector to the dwh-extract plugin - another local CSV, or a new system like BigQuery, Azure Blob Storage, Snowflake, an API. Also covers adding a business rule. Use when someone wants to onboard a source, add a connector, or support a new system.
---

# Add a data source

## A. Another source of an existing type (e.g. one more CSV)

Add an entry to `sources` in `config/sources.json`:

```json
{
  "name": "orders_csv",
  "type": "csv",
  "enabled": true,
  "connection": { "path": "../sample_data/orders.csv", "delimiter": "," },
  "extract": { "mode": "full" },
  "business_rules": ["trim_whitespace", "drop_if_null:order_id"],
  "reconciliation": {
    "control_total_column": "amount",
    "key_columns": ["order_id"],
    "expect_min_rows": 1
  }
}
```

Paths resolve relative to the config file's folder; `~` and `${ENV_VAR}` expand.
Test: `python "${CLAUDE_PLUGIN_ROOT}/scripts/etl_cli.py" extract orders_csv`.

## B. A new connector / source type (BigQuery, Azure Blob, ...)

1. Copy a template in `scripts/etl/extractors/`:
   `bigquery_source.py.example` or `azure_blob_source.py.example` → `<name>_source.py`.
2. Implement `extract(self) -> list[dict]`. Read config from
   `self.source.connection`. **Read secrets from env vars or a secret manager
   inside `extract()` — never from `sources.json`.**
3. Register it in `scripts/etl/extractors/__init__.py`:
   ```python
   from .bigquery_source import BigQueryExtractor
   register("bigquery", BigQueryExtractor)
   ```
4. Add any third-party package to `scripts/requirements.txt`.
5. Confirm: `python "${CLAUDE_PLUGIN_ROOT}/scripts/etl_cli.py" types` lists it.

The rest of the pipeline (rules, landing, manifest, reconciliation) is unchanged —
a connector only has to return rows.

## C. A new business rule

Add a function in `scripts/etl/business_rules.py` decorated with `@rule("name")`,
signature `(rows, arg) -> (kept_rows, rejected_rows)`. Immediately usable as
`"name"` or `"name:arg"` in any source's `business_rules`. Confirm with
`etl_cli.py rules`.
