# 07 - Scheduling & orchestration

> DEMO - fictional.

## Per-pipeline schedule

| Pipeline | Cadence | Deadline / SLA | Upstream dependencies | Catch-up on miss |
|----------|---------|----------------|-----------------------|------------------|
| `pos_ingest` | S3 event sensor (files 02:00-03:30 UTC) + 04:00 sweep | all stores landed by 04:30 UTC | - | yes (per store/dt) |
| `oltp_ingest` | every 4h (00/04/08/12/16/20 UTC) | last pre-close run done 05:00 UTC | - | yes (watermark) |
| `shopify_ingest` | hourly | 05:00 UTC final | - | yes (24h lookback) |
| `salesforce_ingest` | every 6h | 05:00 UTC | - | yes |
| `ga4_extract` | daily 04:00 UTC (D-2 shard) | 04:45 UTC | GA4 export finalised | yes (reprocess shard) |
| `fx_ingest` | daily 05:00 UTC | 05:15 UTC | - | carry-forward |
| `curated_build` (dbt silver+gold) | daily 05:15 UTC | **gold published + reconciled by 06:00 UTC** | all ingests for the business date + `fx_ingest` | rerun business date |
| `publish` + `catalog_register` | after reconcile PASS | 06:00 UTC | `curated_build` recon PASS | - |

## Orchestrator

- **Tool:** **Dagster** (Dagster Cloud, hybrid deployment; agent runs on AWS ECS
  Fargate). Chosen: team has Dagster experience, wants software-defined assets,
  native `dagster-dbt` integration, and asset checks for the reconciliation
  gate. No Airflow (client constraint).
- **Existing deployment we must fit into?** none - greenfield; the ECS agent and
  Dagster Cloud org are provisioned by Terraform (area 10).
- **How pipelines are triggered:** `pos_ingest` by an S3 event sensor; all
  others by cron schedules; `curated_build` by an asset dependency once the
  day's ingest assets are fresh; manual backfill via Dagster backfills UI/CLI.
- **Asset model:** one asset group per source (`ingest/*` -> `bronze` tables),
  the dbt project loaded as assets (`silver/*`, `gold/*`), a `reconcile` asset
  check (blocking), then `publish` and `catalog_register` assets.

## Retry & failure handling

- **Transient errors** (API 429/5xx, S3 throttling, Spark executor loss): max 3
  attempts, exponential backoff (30s, 2m, 8m).
- **Permanent errors** (auth failure, schema drift = fail policy, DQ over
  threshold, reconcile FAIL): stop, no retry, page on-call.
- **Partial failure:** ingest resumes per `(source, business_date[, store])`;
  `curated_build` reruns the whole business date (dbt `merge` is idempotent).

## Backfill

- **How a window is re-run:** `dagster job backfill --partition-range
  2024-01-01...2024-12-31` for ingest assets, then `curated_build` over the same
  range; one `run_id` per business date, watermark untouched until each date
  reconciles.
- **Idempotency guarantee during backfill:** see area 02 - new `run_id` per
  bronze write, dbt `merge` on `unique_key`, snapshots deterministic.

## Alerting

- **Channel:** PagerDuty (page) for SLA breach / reconcile FAIL / permanent
  error; `#northwind-data` Slack for warnings, DQ digests, backfill progress.
- **Triggers:** ingest failure, S3 file missing past 04:30, schema drift, DQ
  over threshold, reconciliation FAIL, `curated_build` not done by 05:45
  (early-warning), cost alarm.
- **Who is notified / paged:** Analytics Eng on-call primary; Data Platform
  on-call secondary for infra/agent issues.
