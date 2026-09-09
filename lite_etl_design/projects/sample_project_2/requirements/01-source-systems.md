# 01 - Source systems

> DEMO - fictional. 6 sources.

## Summary

| Slug | Type | Mode | Volume/day | Cadence | Owner |
|------|------|------|-----------|---------|-------|
| `oltp` | sql (PostgreSQL 14) | incremental | ~300k rows | every 4h | Commerce Platform |
| `shopify` | rest_api | incremental | ~40k orders + refunds | hourly | E-commerce |
| `pos` | object storage (S3 CSV.gz) | file-arrival | ~1.5M rows / 60 files | daily 02:00-03:30 UTC | Retail Ops |
| `salesforce` | rest_api (Bulk API 2.0) | incremental | ~5k records | every 6h | Wholesale |
| `ga4` | bigquery (scheduled extract) | full (prior-day snapshot) | ~20M events -> sessions | daily 04:00 UTC | Marketing |
| `fx_rates` | rest_api | full (reference) | ~170 rows | daily 05:00 UTC | Finance |

---

## Source: `oltp`

- **Subject area / domain:** orders, order_lines, customers, products
- **System of record:** PostgreSQL 14 OLTP (read replica `oltp-ro.internal`)
- **Type:** `sql` (engine: PostgreSQL 14)
- **How we reach it:** read replica host, `northwind` DB, schema `public`;
  tables `customers`, `products`, `orders`, `order_lines`
- **Auth method (reference, not value):** secret scope
  `northwind/<env>/oltp` (fields `host`, `user`, `password`), least-privilege
  read-only role
- **Objects to extract:** the 4 tables above (full column list)
- **Extract mode:** incremental
- **Watermark column:** `updated_at` (timestamptz, UTC) - re-read a 60-min
  lookback to catch late commits
- **Expected volume:** ~300k changed rows/day; ~4 GB full snapshot
- **Source freshness:** replica lag < 5 min; acceptable
- **Format & encoding:** native types via JDBC; UTF-8
- **Known quirks:** schema changes have broken reports before -> schema-drift
  check is mandatory; soft deletes via `is_deleted` flag (no hard deletes)
- **Sample / data dictionary available?** yes - ERD in `intake/` follow-up
- **Downstream use:** `dim_customer`, `dim_product`, `fct_order`, `fct_order_line`

## Source: `shopify`

- **Subject area / domain:** online orders, refunds, fulfillments
- **System of record:** Shopify (Admin REST API `2024-07`)
- **Type:** `rest_api`
- **How we reach it:** `https://northwind.myshopify.com/admin/api/2024-07/`,
  endpoints `orders.json`, `refunds`, `fulfillments`; cursor pagination
  (`Link` header), `updated_at_min` filter
- **Auth method:** secret scope `northwind/<env>/shopify` (field `access_token`);
  private app token, rotated quarterly
- **Objects to extract:** orders (incl. line_items), refunds, fulfillments
- **Extract mode:** incremental on `updated_at_min`; 24h lookback
- **Watermark column:** `updated_at` (RFC3339, UTC)
- **Expected volume:** ~40k orders/day; API rate limit 2 req/s (bucket) -> honour
  `Retry-After`
- **Source freshness:** near real-time; we poll hourly
- **Format & encoding:** JSON; money as strings with `currency`
- **Known quirks:** multi-currency (`presentment` vs `shop` money); partial
  refunds arrive days later as updates to an existing order; test orders flagged
  `test=true` must be dropped
- **Downstream use:** `fct_order`, `fct_refund`, `dim_customer` (online identity)

## Source: `pos`

- **Subject area / domain:** in-store transactions and line items
- **System of record:** store POS vendor export
- **Type:** `object storage` (S3)
- **How we reach it:** `s3://northwind-<env>-inbound/pos/dt=YYYY-MM-DD/store=<id>/txns.csv.gz`
- **Auth method:** IAM role `northwind-<env>-ingest` (bucket read); no keys
- **Objects to extract:** one gzipped CSV per store per day (~60 files)
- **Extract mode:** file-arrival (S3 event -> Dagster sensor)
- **Watermark:** `dt` partition (business date); a file is processed once per
  `(dt, store, file_etag)`
- **Expected volume:** ~1.5M rows/day total; ~25 MB gz/store
- **Source freshness:** files land 02:00-03:30 UTC; a late/again file may arrive
  up to 12:00 UTC with corrections
- **Format & encoding:** CSV, header row, `|`-free comma delimiter, UTF-8,
  `\N` null token; **amounts in minor units (cents)**; `txn_ts` local store time
  + `store_tz` column
- **Known quirks:** partial files re-sent same day (new `file_etag`) - must
  supersede, not append; occasional trailing blank line
- **Downstream use:** `fct_order` (channel = store), `fct_order_line`, `dim_store`

## Source: `salesforce`

- **Subject area / domain:** B2B wholesale accounts, contacts, opportunities
- **System of record:** Salesforce
- **Type:** `rest_api` (Bulk API 2.0)
- **How we reach it:** instance URL + Bulk API jobs for `Account`, `Contact`,
  `Opportunity`, `OpportunityLineItem`
- **Auth method:** secret scope `northwind/<env>/salesforce` (OAuth JWT bearer
  flow; connected-app private key)
- **Objects to extract:** the 4 objects above (selected fields)
- **Extract mode:** incremental on `SystemModstamp`; 2h lookback
- **Watermark column:** `SystemModstamp` (UTC)
- **Expected volume:** ~5k changed records/day
- **Source freshness:** we poll every 6h
- **Format & encoding:** CSV from Bulk API; UTF-8
- **Known quirks:** formula fields excluded; deleted rows via
  `queryAll` + `IsDeleted`; API daily request cap - use Bulk not REST
- **Downstream use:** `dim_account`, `fct_wholesale_opportunity`

## Source: `ga4`

- **Subject area / domain:** web/app session analytics
- **System of record:** GA4 BigQuery export `analytics_310000000.events_*`
- **Type:** `bigquery` via a scheduled extract job (Q1 - resolved: extract, not
  federation)
- **How we reach it:** BigQuery job aggregates prior-day `events_YYYYMMDD` to
  session grain, writes Parquet to `s3://northwind-<env>-inbound/ga4/dt=.../`
- **Auth method:** GCP service account `ga4-reader@...` (BigQuery Data Viewer +
  Job User), key in secret scope `northwind/<env>/gcp`
- **Objects to extract:** aggregated sessions (user_pseudo_id, session_id,
  channel, landing_page, device, events, conversions, revenue)
- **Extract mode:** full snapshot of the prior day
- **Watermark:** `event_date` shard
- **Expected volume:** ~20M raw events -> ~2M session rows/day
- **Source freshness:** GA4 export finalises ~T+1 09:00; we run 04:00 UTC on the
  day-before-yesterday shard to be safe (48h lag accepted)
- **Format & encoding:** Parquet after extraction
- **Known quirks:** late-arriving hits reprocess a shard; `user_pseudo_id` is not
  a customer id (cookie) - join only on hashed email where a `login` event exists
- **Downstream use:** `fct_web_session`, marketing attribution in `gold`

## Source: `fx_rates`

- **Subject area / domain:** daily FX reference rates (base USD)
- **System of record:** `https://open.er-api.com/v6/latest/USD`
- **Type:** `rest_api`
- **How we reach it:** single GET; response has `rates` map + `time_last_update`
- **Auth method:** none (public); optional API key in `northwind/<env>/fx`
- **Objects to extract:** rate per currency per day
- **Extract mode:** full (small); carry forward last known rate on a gap /
  weekend / holiday, flag `is_carried_forward`
- **Watermark:** `rate_date`
- **Expected volume:** ~170 rows/day
- **Known quirks:** endpoint occasionally 503s -> retry; weekends have no new
  rate
- **Downstream use:** `dim_fx_rate`, currency conversion in `silver`/`gold`

---

## Cross-source notes

- **Shared:** `oltp` and `pos` both feed `fct_order` (channels `web` no,
  `store` yes; `web` comes from `shopify`). Channel resolved via `channel_map`
  seed.
- **Order:** `fx_rates` must land before `silver` currency conversion runs;
  Dagster enforces the dependency.
- **Identity:** deterministic customer match = lower(trim(email)) hashed, or
  `loyalty_id` when present. No fuzzy matching (out of scope).
