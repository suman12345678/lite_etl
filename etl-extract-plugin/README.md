# dwh-extract — a minimal, extensible ETL extraction plugin

The **extraction stage** of an ETL/ELT pipeline for a data warehouse, packaged as
a Claude Code plugin. It is deliberately small so you can extend it: one source
type ships enabled (local CSV), one landing zone ships wired (a folder). The
structure is built for adding BigQuery, Azure Blob, Snowflake, APIs, cloud
landing zones, more business rules, and more reconciliation checks.

```
             ┌─────────┐   ┌────────────────┐   ┌──────────┐   ┌────────────┐   ┌───────────────┐
  source ───►│ EXTRACT │──►│ BUSINESS RULES │──►│   LAND   │──►│  MANIFEST  │──►│  RECONCILE    │
 (CSV now,   │connector│   │ transform +    │   │ partitioned│  │ counts,    │   │ landed vs      │
  BQ/Blob    │         │   │ validate; bad  │   │ files in   │  │ control    │   │ source; PASS/  │
  later)     │         │   │ rows → rejects │   │ landing/   │  │ totals     │   │ FAIL + exit 2  │
             └─────────┘   └────────────────┘   └──────────┘   └────────────┘   └───────────────┘
```

---

## Every plugin part, and its job here

| Plugin part | Path | Role in the ETL |
|---|---|---|
| **Manifest** | `dwh-extract/.claude-plugin/plugin.json` | plugin identity / version |
| **Marketplace** | `.claude-plugin/marketplace.json` | makes it installable locally |
| **Command** | `commands/extract.md` | `/extract <source>` — run the pipeline |
| **Command** | `commands/reconcile.md` | `/reconcile <source>` — re-check a landed run |
| **Command** | `commands/etl-status.md` | `/etl-status` — sources, connectors, recent runs |
| **Agent** | `agents/extraction-reviewer.md` | reads a run's manifest + reconciliation and gives a verdict (ACCEPT / INVESTIGATE / RE-RUN) |
| **Skill** | `skills/run-etl-extraction/` | how to run & read the pipeline |
| **Skill** | `skills/add-data-source/` | how to add a source, a connector, or a rule |
| **Hook** | `hooks/hooks.json` | `SessionStart` → prints configured sources + landing zone into context |
| **MCP server** | `.mcp.json` + `scripts/mcp_server.py` | tools `etl_list_sources`, `etl_extract`, `etl_reconcile`, `etl_list_runs` for programmatic / agent-driven runs |
| **Scripts** | `scripts/etl/` | the actual pipeline (pure standard library) |
| **Config** | `config/sources.json` | the landing zone + every source |
| **Sample data** | `sample_data/customers.csv` | so it runs out of the box |

### Script layout

```
scripts/
├── etl_cli.py                 # CLI used by the commands and the hook
├── mcp_server.py              # stdio MCP server (same pipeline, as tools)
├── requirements.txt           # empty for the base; add connector deps here
└── etl/
    ├── config.py              # load sources.json
    ├── business_rules.py      # @rule registry: trim, rename, mask, cast_int, drop_if_null, ...
    ├── landing.py             # folder-based landing zone writer (swap for S3/GCS/Blob)
    ├── reconciliation.py      # 6 checks comparing landed data back to source
    ├── pipeline.py            # orchestrator: extract → rules → land → manifest → reconcile
    └── extractors/
        ├── base.py            # Extractor ABC
        ├── csv_source.py      # the one connector that ships enabled
        ├── __init__.py        # registry: register("csv", CsvExtractor)
        ├── bigquery_source.py.example    # copy → implement → register
        └── azure_blob_source.py.example  # copy → implement → register
```

---

## Install (local)

In Claude Code:

```
/plugin marketplace add C:\Users\sahaa\suman_on_computer\claude\etl-extract-plugin
/plugin install dwh-extract@etl-extract-marketplace
```

Restart if prompted. On start the hook prints the configured sources and landing
zone.

Requires **Python 3.9+** on `PATH` (`python` or `python3`). No pip installs for
the base plugin.

---

## Quick start

```
/extract customers_csv          # run the pipeline for one source
/reconcile customers_csv        # re-run the reconciliation checks
/etl-status                     # sources, connectors, recent runs
```

Or drive the CLI directly (no plugin needed):

```
cd dwh-extract
python scripts/etl_cli.py sources
python scripts/etl_cli.py extract customers_csv
python scripts/etl_cli.py extract --all
python scripts/etl_cli.py reconcile customers_csv
python scripts/etl_cli.py runs --limit 10
```

The sample run: 8 source rows → 1 rejected (`customer_id` is empty, fails
`cast_int`) → 7 landed, reconciliation **PASS**.

### What lands

```
landing/
├── _runs.jsonl                                   # append-only run log
└── customers_csv/2026-09-01/run_YYYYMMDDrun_id/
    ├── data.csv                                  # the landed dataset
    ├── rejects.csv                               # rows dropped by business rules (+ _reject_reason)
    ├── _manifest.json                            # counts, control totals, rules applied
    └── _reconciliation.json                      # every check, PASS/FAIL, expected vs actual
```

---

## `config/sources.json` reference

```jsonc
{
  "landing_zone": "../landing",          // folder path, or set env ETL_LANDING_ZONE
  "sources": [
    {
      "name": "customers_csv",           // unique id, used everywhere
      "type": "csv",                     // which connector (see `etl_cli.py types`)
      "enabled": true,
      "connection": {                    // connector-specific; NO secrets here
        "path": "../sample_data/customers.csv",
        "delimiter": ",",
        "encoding": "utf-8"
      },
      "extract": {
        "mode": "full",                  // "full" | "incremental" (see Extending)
        "watermark_column": null         // column to track for incremental pulls
      },
      "business_rules": [                 // applied in order; see `etl_cli.py rules`
        "trim_whitespace",
        "rename:cust_id->customer_id",
        "cast_int:customer_id",
        "drop_if_null:customer_id",
        "upper:country",
        "mask:email"
      ],
      "reconciliation": {
        "control_total_column": "balance",  // numeric column whose sum must be conserved
        "tolerance": 0.01,
        "key_columns": ["customer_id"],     // must be non-null in landed data
        "expect_min_rows": 3
      }
    }
  ]
}
```

Paths resolve **relative to the config file's folder**; `~` and `${ENV_VAR}` expand.

### Business rules (built in)

`trim_whitespace` · `rename:old->new` · `upper:col` · `lower:col` · `mask:col`
(light PII masking) · `cast_int:col` (bad values → rejects) · `drop_if_null:col`
(null/empty → rejects). Add your own — see below.

### Reconciliation checks

| Check | Meaning |
|---|---|
| `row_conservation` | `rows_extracted == rows_written + rows_rejected` |
| `min_rows_written` | landed row count ≥ `expect_min_rows` |
| `control_total_conservation[col]` | `sum(landed) + sum(rejected) ≈ source total` — nothing silently lost in transform |
| `source_stability[col]` | re-reading the source now gives the same total (source didn't move under us) |
| `landed_key_not_null` | `key_columns` populated in `data.csv` |
| `data_file_present` | `data.csv` exists |

`status: FAIL` → CLI exits **2**. Use that to gate the downstream warehouse load.

---

## Extending it (the point of this plugin)

### 1. Add another source of an existing type
Add an entry to `sources` in `config/sources.json`. Test with
`python scripts/etl_cli.py extract <name>`. (Skill: **add-data-source**.)

### 2. Add a new connector (BigQuery, Azure Blob, Snowflake, API…)
1. `cp scripts/etl/extractors/bigquery_source.py.example scripts/etl/extractors/bigquery_source.py`
2. Implement `extract(self) -> list[dict]`; read config from `self.source.connection`.
3. Register in `scripts/etl/extractors/__init__.py`:
   `register("bigquery", BigQueryExtractor)`
4. Add the dependency to `scripts/requirements.txt` and `pip install -r`.
5. `python scripts/etl_cli.py types` should list it.

The pipeline downstream of `extract()` is unchanged — a connector only returns rows.

### 3. Add a business rule
Add a `@rule("name")` function in `scripts/etl/business_rules.py`, signature
`(rows, arg) -> (kept, rejected)`. Usable immediately as `"name"` / `"name:arg"`.

### 4. Add a reconciliation check
Add an `add(...)` call in `scripts/etl/reconciliation.py`. Drive its parameters
from the source's `reconciliation` block so it's per-source configurable.

### 5. More landing zones
- **Another folder:** set `landing_zone` per environment, or the `ETL_LANDING_ZONE`
  env var (wins over the file).
- **Cloud object storage:** replace the body of `write_dataset()` / `write_json()`
  in `scripts/etl/landing.py` with an upload (`boto3` / `google-cloud-storage` /
  `azure-storage-blob`). Keep the `<source>/<date>/<run_id>/` key layout — the
  manifest, reconciliation, and run log don't change.

### 6. Incremental extraction
Set `extract.mode` to `"incremental"` and `watermark_column`. In your connector,
read the last watermark (e.g. from the previous run's `_manifest.json` or a small
state file / table) and add a predicate to the query. Record the new high-water
mark in the manifest.

### 7. Secrets
Never in `sources.json`. Read them inside `extract()` from environment variables
or a secret manager (GCP Secret Manager, Azure Key Vault, AWS Secrets Manager).
`connection` should hold only non-sensitive coordinates (project, dataset, URL,
container, prefix).

---

## Running it the enterprise / automated way

- **Schedule** `python scripts/etl_cli.py extract --all` from cron, Windows Task
  Scheduler, Airflow (`BashOperator`), Dagster, Prefect, or a CI job (GitHub
  Actions / GitLab CI). One command extracts every enabled source.
- **Gate the load on reconciliation.** The CLI exits **2** when any check fails.
  ```bash
  python scripts/etl_cli.py extract --all && python load_to_warehouse.py
  ```
  A non-zero exit stops the chain; alert on it.
- **Idempotency & replay.** Every run lands under its own `run_id` partition;
  re-running never overwrites. Downstream loads should be keyed on `run_id`.
- **Observability.** Ship `landing/_runs.jsonl` to your log platform; load each
  `_manifest.json` / `_reconciliation.json` into an `etl_run` metadata table for
  freshness and row-count dashboards.
- **Config as code.** Keep `config/sources.json` in version control; validate it
  in CI (`python -c "import json; json.load(open('dwh-extract/config/sources.json'))"`)
  and require review to onboard a source.
- **Per-environment landing zones.** Set `ETL_LANDING_ZONE` (and `ETL_CONFIG`) per
  environment; the same code promotes dev → prod unchanged.
- **Agent/LLM orchestration.** The MCP server (`etl_extract`, `etl_reconcile`, …)
  lets an agent trigger and inspect runs; pair it with the `extraction-reviewer`
  agent for an automatic written verdict on each run.
- **Onboarding a source in a PR:** add the `sources.json` entry (+ a connector
  file if it's a new type), run `python scripts/etl_cli.py extract <name>` locally,
  attach the `_reconciliation.json`, merge.

---

## Test

```
cd dwh-extract
python -m py_compile scripts/etl_cli.py scripts/mcp_server.py scripts/etl/*.py scripts/etl/extractors/*.py
python scripts/etl_cli.py extract customers_csv     # expect reconciliation PASS, exit 0
```
