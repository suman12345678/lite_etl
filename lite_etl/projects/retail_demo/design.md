# Design — retail_demo

## Approach
ELT: land raw -> dbt (`<engine>`) -> rule checks -> publish.
Orchestrator: cron (one daily run after the FX file arrives).   Infra: Terraform.

The bundled local demo (`repo/demo/`) runs the whole flow on **SQLite from the Python
standard library** — no cloud, no pip install. The transform SQL in `demo/sql/` is the
same SQL used as the dbt model bodies, so what you see locally is what runs on the warehouse.

## Components
| component | does | spec ref |
|-----------|------|----------|
| extract/oltp | pull `orders` + `customers` -> raw | Sources |
| extract/fx | pull the daily FX rates csv -> raw | Sources |
| dbt · staging | raw -> `stg_*`: snake_case, cast dates, drop test rows, hash email, dedupe orders | Target, Transforms |
| dbt · marts | `stg_*` -> `dim_customer`, `fct_order`: FX carry-forward join, `net_usd` | Target, Transforms |
| rules | run `rules.yml`: quality checks (warn/quarantine/fail) + PII guard + web-GMV reconcile (block) | Rules |
| publish | write `gold/` + `_SUCCESS` + advance the `order_date` watermark, or block and exit 1 | Target, Schedule |
| infra | `engine` (duckdb \| databricks \| snowflake), storage bucket, warehouse/catalog, roles — one Terraform module, one `envs/<env>` per env | Non-functional, envs |
| ci | lint · `make demo` · `make demo-fail` · `dbt build --target ci` · `terraform validate` | envs |

## Data flow
see diagram.md

## Decisions
- **Local demo runs on SQLite (stdlib)** because the spec asks for the smallest possible thing to
  run on stage — `python -m demo.run` needs only Python. The same `demo/sql/*.sql` files are the
  dbt model bodies, so the demo is faithful to the warehouse run.
- **`engine` is a single Terraform variable** with allowed values `duckdb | databricks | snowflake`
  because every transform is plain dbt SQL and every rule is warehouse-agnostic — only the
  connection profile and two macros change. This is the "swap to Snowflake / Databricks" seam.
- **One `rules.yml` for data quality *and* reconciliation** because the spec's Rules section keeps
  them together; `demo/rules.py` runs it locally, dbt tests + the publish gate run it in prod.
- **FX gaps → carry forward the last known rate** because Sources notes weekend / holiday gaps in
  `fx.rates`.
- **PII (`email`) is hashed at the staging boundary** and a marts-wide "no raw email" check runs as
  a `fail` rule, because pii handling in Non-functional requires the raw value never reaches marts.
- **Quarantine vs block**: row-level quality problems (`net_usd < 0`, unknown currency) divert the
  row to `reject_fct_order` and the run continues; a reconciliation break means the whole publish is
  wrong, so it blocks and exits non-zero.

## Maps to spec
- Sources → extract/oltp, extract/fx, dbt·staging
- Target (zones, `dim_customer`, `fct_order`, keys) → dbt·staging, dbt·marts, publish
- Transforms (snake_case, cast, drop test rows, dedupe, FX carry-forward join, `net_usd`, hash email) → dbt·staging + dbt·marts
- Rules (4 quality + PII guard + web-GMV reconcile) → rules, publish
- Schedule (daily cron, backfill by date range, idempotent replace) → publish, ci
- Non-functional (volume, latency, pii, envs) → infra, dbt·staging (hash), ci

Gaps: none. (Prod engine choice is deferred by design — it is an infra variable, not a pipeline change.)
