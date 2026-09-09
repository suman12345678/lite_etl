# 07 - Scheduling & orchestration

## Per-pipeline schedule

| Pipeline | Cadence | Deadline / SLA | Upstream dependencies | Catch-up on miss |
|----------|---------|----------------|-----------------------|------------------|
| | hourly / daily / event / continuous | e.g. done by 06:00 UTC | | yes / no |

## Orchestrator

- **Tool:** Airflow / Dagster / Prefect / cron / Azure Data Factory /
  Step Functions / cloud-native / **to be recommended**
- **Existing deployment we must fit into?**
- **How pipelines are triggered:** schedule / sensor / file event / API / manual

## Retry & failure handling

- **Transient errors:** max attempts, backoff
- **Permanent errors:** stop and alert (no retry)
- **Partial failure:** resume per partition / restart whole run

## Backfill

- **How a window is re-run:** command / parameters
- **Idempotency guarantee during backfill:** (link to 02)

## Alerting

- **Channel:** email / Slack / PagerDuty / other
- **Triggers:** run failure / SLA breach / reconciliation FAIL / DQ threshold /
  schema drift
- **Who is notified / paged:**
