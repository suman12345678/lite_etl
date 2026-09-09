# 02 - Targets & loading

> DEMO - fictional.

## Target platform

- **Platform:** Databricks lakehouse (Unity Catalog, Delta Lake) on AWS
- **Target catalog / schemas:** catalog per env - `northwind_dev`,
  `northwind_stg`, `northwind_prd`; schemas `bronze`, `silver`, `gold`, and a
  restricted `gold_pii`
- **Naming conventions:** `bronze.<source>__<object>` (landed, 1:1 with source);
  `silver.stg_<source>__<entity>` and `silver.int_<domain>__<step>`;
  `gold.dim_*` / `gold.fct_*`; `gold_pii.dim_customer_pii`
- **Region / account:** AWS `eu-west-1`; separate AWS account for `prd`

## Landing / staging zone

- **Required?** yes - `bronze` is the immutable landing zone (Delta external
  tables over S3)
- **Location:** `s3://northwind-<env>-lakehouse/bronze/<source>/<object>/`;
  raw inbound files stay in `s3://northwind-<env>-inbound/`
- **Format:** Delta (underlying Parquet + Snappy); inbound files as delivered
  (CSV.gz / JSON / Parquet)
- **Layout:** `bronze` tables partitioned by `_ingest_date`; each write records
  `_run_id`, `_source_file`, `_extracted_at`, `_ingest_date`
- **Retention:** `bronze` 60 days then `VACUUM` + purge inbound; `silver` 90
  days history via snapshots; `gold` 5 years; `gold_pii` 25 months

## Load patterns

| Target table | Pattern | Business key | Surrogate key? | Partition / cluster | Notes |
|--------------|---------|--------------|----------------|---------------------|-------|
| `gold.dim_customer` | SCD type 2 (dbt snapshot -> dim) | `customer_bk` (hashed email or loyalty_id) | `customer_sk` = `dbt_utils.generate_surrogate_key` | ZORDER by `customer_bk` | non-PII attrs only; hashed email; real PII in `gold_pii.dim_customer_pii` |
| `gold.dim_product` | SCD type 2 | `product_id` | `product_sk` | ZORDER by `product_id` | price, category, brand history |
| `gold.dim_store` | SCD type 2 | `store_id` | `store_sk` | small | from `store_master` seed + POS observed |
| `gold.dim_account` | SCD type 2 | `sfdc_account_id` | `account_sk` | small | wholesale accounts |
| `gold.dim_fx_rate` | upsert (merge) | `(rate_date, currency)` | - | partition by `rate_date` | `is_carried_forward` flag |
| `gold.dim_date` | static seed / generated | `date_key` | - | - | 2015-2035 |
| `gold.fct_order` | incremental `merge` | `order_id` (+ `channel`) | - | partition by `order_date`, ZORDER by `customer_sk` | one row per order header; `web`/`store`/`wholesale` |
| `gold.fct_order_line` | incremental `merge` | `(order_id, line_no)` | - | partition by `order_date` | grain: order line |
| `gold.fct_refund` | incremental `merge` | `refund_id` | - | partition by `refund_date` | links to `fct_order` |
| `gold.fct_web_session` | incremental `insert` (append, idempotent per `session_date`) | `(session_id, session_date)` | - | partition by `session_date` | GA4 sessions |
| `gold.fct_wholesale_opportunity` | incremental `merge` | `opportunity_id` | - | partition by `close_date` | SFDC opportunities |
| `gold_pii.dim_customer_pii` | SCD type 2 | `customer_bk` | `customer_sk` (same as dim) | ZORDER by `customer_bk` | real email/phone/name/address/DOB; UC row filter + column mask |

## Idempotency & replay

- **Run identity:** `run_id` (uuid) per source per business date; carried in
  every `bronze` row and in the Dagster run tags and dbt `invocation_id`
- **Re-run safety:**
  - `bronze` - a re-run writes a **new** `run_id`; for `pos`, a superseding
    `file_etag` marks prior rows `_superseded = true` (kept, not deleted)
  - `silver`/`gold` - dbt incremental models `merge` on `unique_key`; re-running
    a business date replaces exactly that date's rows. Snapshots are
    deterministic on `updated_at`.
- **Rollback:** `gold` publish per business date is one Databricks transaction
  per table group; on failure nothing commits. Delta `RESTORE` / time-travel
  covers a bad publish already consumed.
- **Watermark advance:** an incremental source advances its stored watermark
  **only after** the business date reconciles PASS and `gold` is published.
  Failure => watermark unchanged, next run re-reads the window.

## Backfill at go-live

- **Needed?** yes - 24 months for `oltp`, `shopify`, `pos` (Q2 assumption: 24
  months, pending Finance). One business date per run, oldest first, same
  idempotent path. Estimated ~1.1 TB POS history + ~140 GB Shopify. Run over a
  weekend on a larger job cluster, then resume the normal schedule.
- GA4: 13 months of aggregated sessions (BigQuery retention permitting).
- Salesforce + FX: current snapshot only.
