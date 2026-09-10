# Spec — retail_demo

engine: duckdb | databricks | snowflake      <!-- duckdb = local demo; the bundled runnable demo uses SQLite (Python stdlib, zero install) -->
owner: suman    date: 2026-09-09

## Sources
| name | kind | grain | load | quirks |
|------|------|-------|------|--------|
| oltp.orders | postgres | row | incremental | amounts in local currency; late/duplicate rows re-sent with newer `loaded_at`; test rows have email `%@example.test` |
| oltp.customers | postgres | row | full | contains PII (`email`); we keep latest row per customer |
| fx.rates | s3-file (csv) | row | full daily | one rate per currency per day; weekend / holiday gaps → carry forward last known rate |

## Target
- zones: raw -> staging -> marts
- model:
  - `dim_customer`  — grain: one row per `customer_id`; PII (`email`) stored only as `email_sha256`
  - `fct_order`     — grain: one row per `order_id`; money in USD (`net_usd`), plus `channel`, `order_date`
- keys: `customer_id` (dim), `order_id` (fact)

## Transforms
- cast `order_ts` -> `order_date`; rename all columns to snake_case
- drop test rows: `lower(email) like '%@example.test'`
- dedupe `orders` on `order_id`, keep the row with the latest `loaded_at`
- join `fx.rates` on `(currency, order_date)`; if no rate that day, use the most recent prior rate (carry forward)
- `net_usd = round(amount_local * rate_to_usd, 2)`
- hash `customer.email` -> `email_sha256` (sha256); raw `email` never reaches marts

## Rules
<!-- these become repo/rules.yml -->
- quality: `fct_order.order_id` is not null                       on_fail: fail
- quality: `fct_order.net_usd >= 0`                               on_fail: quarantine
- quality: `fct_order.currency` in the known currency list        on_fail: quarantine
- quality: no marts column contains a raw email (`'%@%'`)         on_fail: fail        <!-- PII guard -->
- reconcile: `sum(net_usd) where channel='web'` vs finance control total   tolerance 0.5%   on_fail: block

## Schedule
- cadence: daily 06:00, after the FX file lands; deadline 07:00
- backfill: `python -m demo.run --date-range <start> <end>` re-runs one day at a time; publish is idempotent replace per `order_date`

## Non-functional
- volume: demo ~200 orders/run; real target millions/day, ~5 GB/day growth   latency: curated data ready < 15 min   cost: n/a (demo)
- pii: `customer.email` → sha256 hash at the staging boundary; raw value never lands in staging or marts
- envs: dev, prod

## Open questions
- Prod warehouse is not yet fixed (Databricks vs Snowflake). The pipeline is engine-agnostic — dbt models + `rules.yml` are unchanged; only the Terraform `engine` variable and the dbt profile differ. Decide at the infra layer.
