# 07 - Scheduling & orchestration

> DEMO - fictional.

## Per-pipeline schedule

| Pipeline | Cadence | Deadline / SLA | Upstream dependencies | Catch-up on miss |
|----------|---------|----------------|-----------------------|------------------|
| `fx_rates_daily` | daily 16:30 CET + retry 20:00 | rate for date available before 22:00 | ECB publication | yes (carry-forward if still missing) |
| `reference_refresh` | daily 00:30 CET | before dims build | none | yes |
| `core_banking_daily` | daily 02:00 CET | staged by 03:30 | reference_refresh | yes, per business_date |
| `customer_master_daily` | daily 02:00 CET | staged by 03:30 | reference_refresh | yes |
| `card_transactions_daily` | file sensor from 01:30, timeout 03:30 CET | landed by 04:00 | file arrival; dims current | yes, per business_date |
| `general_ledger_daily` | daily 01:00 CET | staged by 02:30 | BQ replica complete | yes |
| `curated_build` (dbt) | daily 04:15 CET | **CURATED PASS + sign-off by 06:00 CET** | all of the above for the business date | yes |
| `regulatory_extract_handoff` | daily 06:15 CET | file to reg engine by 07:00 CET | curated_build PASS | no - manual re-trigger |

## Orchestrator

- **Tool:** **Apache Airflow** on **Amazon MWAA** (managed) - 2 engineers already
  know it; managed fits the "prefer managed services" constraint
- **Existing deployment:** none - new MWAA environment per AWS account
  (dev / uat / prod)
- **How pipelines are triggered:** time schedule for most; an **S3 key sensor**
  (or SFTP poll -> S3) for `card_transactions_daily`; `curated_build` triggered
  by an ExternalTaskSensor / dataset dependency on all source DAGs for the
  business date

## Retry & failure handling

- **Transient errors** (connection, throttling, S3 5xx): max 3 attempts,
  exponential backoff (1m, 5m, 15m)
- **Permanent errors** (auth, schema drift, DQ over threshold, reconciliation
  FAIL): no retry - fail the task, alert, business date stays open
- **Partial failure:** extract/land are restartable per source and per file
  part; `curated_build` is all-or-nothing per business date (single transaction)

## Backfill

- **Command:** `etl backfill <source> --from <date> --to <date>` (one
  `business_date` per run, oldest first); `curated_build --business-date <date>`
  after each source set completes
- **Idempotency guarantee:** identical to normal runs - new `run_id`, prior rows
  for the `business_date` removed before insert, watermark untouched during
  backfill (see `02`)

## Alerting

- **Channels:** PagerDuty (Sev2) for SLA breach / reconciliation FAIL / DQ block;
  Slack `#risk-data-ops` for warnings, drift, carry-forward FX, quarantine growth
- **Triggers:** run failure, SLA deadline missed, reconciliation FAIL, DQ over
  threshold, source schema drift, card file late/missing at 03:30
- **Notified:** Risk Data on-call (primary), Data Platform (secondary); Finance
  Systems additionally on GL tie-out warnings
