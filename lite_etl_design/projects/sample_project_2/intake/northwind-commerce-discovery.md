# Northwind Commerce - discovery notes

> Raw material handed over before the interview. Dropped into `intake/` so the
> `/gather-requirements` interview reads it first and only asks about gaps.
>
> **Fictional - for harness demo purposes only.**

## Background

Northwind Commerce is a UK-based omnichannel retailer: ~60 physical stores, a
Shopify online store, and a B2B wholesale arm. ~2M customers. Analytics today is
a mix of spreadsheets and an ageing Redshift cluster that Finance and Marketing
both distrust ("the numbers never match Shopify"). They have bought Databricks
and want a governed lakehouse with a trusted `gold` layer that feeds Looker
(BI), Braze (marketing, via reverse-ETL), and the Finance close.

## What they told us in discovery

- **OLTP is PostgreSQL 14** (orders, order_lines, customers, products). A
  read-replica is available. They think ~300k rows change per day. Every table
  has `updated_at` (timestamptz, stored UTC).
- **Online orders + refunds** come from the **Shopify Admin REST API**. They have
  an app with an access token. Multi-currency (CAD, GBP, EUR as well as USD).
  ~40k orders/day. Pagination is a pain.
- **Store POS** drops a **gzipped CSV per store per day** to an S3 bucket around
  02:00-03:30 UTC (`pos/dt=YYYY-MM-DD/store=<id>/txns.csv.gz`). ~1.5M rows/day.
  Amounts are in **cents/pence**. Sometimes a store's file is re-sent later the
  same day with corrections.
- **Wholesale** lives in **Salesforce** (Accounts, Contacts, Opportunities).
  Bulk API is fine. ~5k records change per day. `SystemModstamp` is the
  watermark.
- **Web analytics** is **GA4, exported to BigQuery** (daily sharded
  `events_YYYYMMDD` tables). We only need daily session-level aggregates, not
  raw events.
- **FX rates** - they currently paste rates into a sheet. There's a free daily
  REST endpoint.
- Reporting currency is **USD**. Stores are USD-equivalent already; Shopify and
  wholesale need conversion.
- **gold must be ready by 06:00 UTC** - Looker refreshes at 06:30.
- They are **UK GDPR** regulated. Customer email, phone, name, address, DOB are
  in scope. Marketing needs to segment on hashed email; only a small team may
  see real PII.
- The data team knows **Python, SQL and dbt** well. Two engineers have used
  **Dagster**; nobody wants Airflow again.
- They want **infrastructure as code** - "if it's not in Terraform it doesn't
  exist" is a platform-team rule.
- Run-cost guidance: **keep Databricks + AWS + orchestration under $6k/month**.
- dev / staging / prod must be properly separated; prod is a locked-down AWS
  account.

## Known pain points they listed

1. Shopify totals never reconcile with the finance numbers - nobody knows which
   is right.
2. POS corrections re-sent mid-day cause double counting downstream.
3. No lineage - when Looker shows a weird number, tracing it is guesswork.
4. Re-running a day's load currently duplicates rows.
5. Schema changes in the Postgres OLTP have silently broken reports twice.

## Out of scope (client stated)

- Real-time / streaming (same-day batch is fine).
- The Looker model itself and the Braze reverse-ETL job (they own those; we just
  publish a clean `gold`).
- Replacing Salesforce or the POS system.
- Customer-360 identity resolution beyond a deterministic email/loyalty-id match.
