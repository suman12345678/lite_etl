# 02 - Targets & loading

> DEMO - fictional.

## Target platform

- **Platform:** Snowflake
- **Target database / schemas:** `RISK_DWH` with schemas `RAW`, `STAGING`,
  `CURATED`, and a restricted `CURATED_SENSITIVE` (real PII, row-access policy)
- **Naming conventions:** `DIM_*`, `FACT_*`, `BRG_*` in `CURATED`;
  `STG_<source>_<object>` in `STAGING`; `RAW.<source>__<object>` mirrors landing
- **Region / account:** Snowflake account per environment (`_DEV`, `_UAT`, `_PRD`);
  AWS `eu-central-1`

## Landing / staging zone

- **Required?** yes - object storage landing before Snowflake
- **Location:** S3 `s3://meridian-riskdwh-<env>-landing/`
- **Format:** Parquet (Snappy)
- **Layout:** `<domain>/<source>/business_date=YYYY-MM-DD/run_id=<uuid>/data-*.parquet`
  plus `manifest.json`, `rejects.parquet`, `_reconciliation.json`, `_SUCCESS`
- **Retention:** landing (RAW zone) 90 days, then purge; curated 7 years (SOX / regulatory)

## Load patterns

| Target table | Pattern | Business key | Surrogate key? | Partition / cluster | Notes |
|--------------|---------|--------------|----------------|---------------------|-------|
| `DIM_ACCOUNT` | SCD type 2 | `account_id` | `account_sk` = sha256(account_id) | cluster by `account_id` | track product, status, currency, branch |
| `DIM_CUSTOMER` | SCD type 2 | `customer_id` | `customer_sk` | cluster by `customer_id` | non-sensitive attrs in CURATED; name/DOB/nat-id tokenised here, real values only in `CURATED_SENSITIVE` |
| `DIM_FX_RATE` | upsert (merge) | `(rate_date, ccy)` | - | cluster by `rate_date` | carry-forward rows flagged `is_carried_forward` |
| `FACT_ACCOUNT_BALANCE_DAILY` | snapshot (insert per business_date) | `(account_id, business_date)` | - | partition/cluster by `business_date` | one row per account per day |
| `FACT_CARD_TXN` | append (insert), dedup on load | `(txn_id, post_date)` | - | cluster by `post_date` | immutable once loaded; late corrections arrive as new `txn_id` |
| `FACT_GL_BALANCE` | snapshot (insert per business_date) | `(gl_account, cost_centre, business_date)` | - | cluster by `business_date` | source of GL tie-out |

## Idempotency & replay

- **Run identity:** `run_id` (uuid) per source per business date; recorded in
  `manifest.json` and every RAW/STAGING row (`_run_id` column)
- **Re-run safety:** a re-run for a `(source, business_date)` writes a **new**
  `run_id` folder; the loader deletes/ignores prior rows for that
  `business_date` before insert (facts) or re-evaluates SCD2 from the latest
  snapshot (dims). Net effect: identical output, no double counting.
- **Rollback:** publish to `CURATED` is a single transaction per business date;
  on failure nothing is committed. Snowflake Time Travel covers accidental commits.
- **Watermark advance:** incremental sources advance their watermark **only after
  the business date reconciles PASS and is published**. Failure => watermark
  unchanged, next run re-reads the window.

## Backfill at go-live

- **Needed?** yes - 13 months of history for card transactions and daily
  balances (regulatory look-back). Backfill runs one `business_date` per run,
  oldest first, same idempotent path. Estimated ~1.9 TB card history; run over a
  weekend with increased warehouse size, then resume normal schedule.
