# Observability wiring

> Phase 5 deliverable. What the pipeline emits, where it goes, what "healthy"
> means, and which conditions page. From `requirements/07` (alerting) and `09`
> (observability) and `design/component-design.md` (observability component).

## Metrics

| Metric | Source | Dimensions | Used for |
|--------|--------|-----------|----------|
| rows in / out | each component + dbt | source, entity, run_id | volume anomaly |
| bytes landed | landing writer | source, business_date | cost, volume |
| run duration | orchestrator | pipeline, task | SLA tracking |
| freshness lag | `dbt source freshness` | source | staleness alert |
| reject rate | DQ engine | entity, rule | DQ health |
| reconciliation delta | reconciliation engine | check, channel | gate health |
| compute spend / DBU / slots | warehouse system tables | env, warehouse | budget alert |
| gate result | reconciliation | pipeline, business_date | publish audit |

## Logs

- **Format:** structured JSON; every line carries `run_id`, `pipeline`,
  `business_date`, `component`.
- **Destination / retention:** (from `09`)
- **Correlation:** `run_id` links extractor logs -> dbt `invocation_id` ->
  orchestrator run -> reconciliation report.

## Dashboards

| Dashboard | Panels | Audience |
|-----------|--------|----------|
| Pipeline health | asset/task status per business date, SLA countdown, last gate result | on-call |
| Data quality | per-rule pass rate, reject rate trend, anomalies | Analytics Eng |
| Cost | spend vs budget, per-pipeline compute, storage growth | Platform / FinOps |
| Freshness | lag per source vs its SLA | on-call |

## Alert rules

| Condition | Severity | Channel | Who |
|-----------|----------|---------|-----|
| extract failure (after retries) | page | PagerDuty | on-call |
| file missing past deadline | page | PagerDuty | on-call |
| schema drift (policy = fail) | page | PagerDuty | on-call + source owner |
| DQ reject rate > fail threshold | page | PagerDuty | on-call |
| reconciliation FAIL | page | PagerDuty | on-call |
| SLA breach (not published by `<time>`) | page | PagerDuty | on-call |
| DQ in warn band / anomaly | warn | Slack | Analytics Eng |
| cost > `<n>%` of budget | warn | Slack | Platform |
| drift plan non-empty | warn | Slack + issue | Platform |

## SLOs

| SLO | Target | Window |
|-----|--------|--------|
| `gold` published by `<time>` | `<x>%` of days | 30 days |
| zero unreconciled publishes | 100% | always |
| freshness within SLA per source | `<x>%` | 30 days |

## "Healthy pipeline" definition

_All ingest fresh for the business date, transform + tests green, reconciliation
PASS, published before the SLA, spend on track._ (Restate from `09`.)

## Wiring checklist

- [ ] every metric above has an emit point in code / dbt / IaC
- [ ] alert routes exist in the `observability` Terraform module
- [ ] dashboards defined as code where the platform allows
- [ ] a synthetic failure of each paging condition has been fired once in dev
