# Observability wiring - Northwind Commerce (DEMO)

> Phase 5 deliverable. What the pipeline emits, where it goes, what "healthy"
> means, and which conditions page. From `requirements/07` (alerting) + `09`
> (observability) + `design/component-design.md` (`observability`) +
> `pipeline/orchestration-wiring.md` (alert routing).

## Metrics

| Metric | Source | Dimensions | Used for | Emit point |
|--------|--------|-----------|----------|------------|
| `rows_in` / `rows_out` | each extractor + every dbt model | `source`, `entity`, `run_id`, `business_date` | volume anomaly (Elementary) | `obs.metrics.emit`; dbt `on-run-end` + Elementary |
| `bytes_landed` | landing writer | `source`, `business_date` | cost + volume | `extractors.common.landing.write` |
| `run_duration_s` | Dagster | `pipeline`, `asset`, `business_date` | SLA tracking, runtime budget (`09`) | Dagster run/asset events -> CloudWatch |
| `freshness_lag_s` | `dbt source freshness` | `source` | staleness alert (DQ14) | `source_freshness` gate asset (**TODO** scaffold, `/validate-config` #15) |
| `reject_count` / `reject_rate` | DQ engine / dbt tests | `entity`, `rule`, `business_date` | DQ health, threshold routing | singular tests + `reject__<entity>` counts |
| `dq_score` | Elementary | `model` | 7-day pass-rate trend, target `>= 99.5%` (`04`) | Elementary |
| `recon_delta` | `recon/gate.py` | `check`, `channel`/`store_id`, `business_date` | gate health, drift trend | `_reconciliation.json` -> metrics + Elementary row |
| `gate_result` | `reconcile` asset check | `pipeline`, `business_date` | publish audit (PASS/FAIL/BLOCKED) | `northwind_dagster/checks/reconcile.py` |
| `publish_success` | publisher | `business_date` | 06:00 SLA alarm | `_SUCCESS` write -> custom CloudWatch metric `Northwind/Pipeline` |
| `stale_sources` | `source_freshness` | `business_date` | freshness alarm | count of sources past `error_after` |
| `dbu_spend` / `compute_cost_usd` | Databricks system tables + AWS Cost | `env`, `warehouse`, `day` | budget alarm at 80% of $6k (`09`) | scheduled query -> CloudWatch |
| `storage_bytes` | S3 + Delta system tables | `zone` (`bronze`/`silver`/`gold`/`gold_pii`) | storage growth vs the ~2.6 TB/12mo projection | nightly |
| `backfill_progress` | `backfill.py` / Dagster backfill | `partition_range` | backfill tracking | Dagster backfill events |

## Logs

- **Format:** structured JSON (`structlog`, already a Phase 3 dep). Every line
  carries `run_id`, `pipeline`, `business_date`, `component`, and where relevant
  `source` / `entity` / `dbt_invocation_id`.
- **Destinations / retention (`09`):** Dagster run logs -> S3 + CloudWatch,
  **13 months**; dbt logs as Dagster run artifacts; extractor logs JSON to
  CloudWatch. `_recon` reports -> S3 **5 years**; run manifests per `06`.
- **Correlation chain:** extractor `run_id` -> dbt `invocation_id`
  (in `run_results.json`) -> Dagster run id -> `_reconciliation.json.run_id` ->
  `_SUCCESS` marker. One `run_id` per business date (new on each re-run/backfill).

## Dashboards

| Dashboard | Panels | Audience | Built as |
|-----------|--------|----------|----------|
| **Pipeline health** | asset/task status per business date, SLA countdown to 06:00, last `gate_result`, run duration vs budget | on-call | Dagster UI + a Databricks SQL panel |
| **Data quality** (Elementary) | per-rule pass rate, `reject_rate` trend, `dq_score` 7-day, Elementary anomalies | Analytics Eng | Elementary report (S3 static site + Databricks) |
| **Cost** | `dbu_spend` vs $6k budget, per-pipeline compute, `storage_bytes` growth | Platform / FinOps | Databricks SQL + CloudWatch |
| **Freshness** | `freshness_lag` per source vs its `warn_after` / `error_after` | on-call | Databricks SQL |

Dashboards defined as code where the platform allows (Databricks SQL dashboard
JSON in `infra/` or `dbt/`; the Elementary report is generated). CloudWatch
dashboard JSON is in the `observability` Terraform module (`cicd`/`iac-plan.md`).

## Alert rules

| # | Condition | Severity | Channel | Who | Maps to |
|---|-----------|----------|---------|-----|---------|
| A1 | extract failure after 3 retries | page | PagerDuty | Analytics Eng on-call (primary) | `07`; `component-design.md` extractor |
| A2 | POS file missing past 04:30 | page | PagerDuty | on-call + POS source owner | `07`; `05` control report |
| A3 | schema drift, policy = fail | page | PagerDuty | on-call + source owner | DQ15; `04` |
| A4 | DQ reject rate `> 0.5%` for any entity, or any error generic test fails | page | PagerDuty | on-call | `04` thresholds; `dq-behaviour-matrix.md` |
| A5 | reconciliation FAIL (any of the 8 checks) | page | PagerDuty | on-call | `05`; `reconciliation-fixtures.md` |
| A6 | `curated_build` not done by **05:45** UTC | **warn** (early warning) | Slack `#northwind-data` | on-call | `07` alert points; `pipeline-blueprint.md` |
| A7 | SLA breach - not published by **06:00** UTC (`publish_success` absent) | page | PagerDuty | on-call | `09` latency; `07` |
| A8 | DQ in warn band (`0.1-0.5%`) or Elementary anomaly | warn | Slack `#northwind-data` | Analytics Eng | `04` |
| A9 | cost `> 80%` of the $6k monthly budget | warn | Slack `#northwind-platform` | Platform | `09` cost |
| A10 | `drift.yml` plan non-empty | warn | Slack `#northwind-platform` + GitHub issue | Platform | `deployment-and-iac.md` s.7 |
| A11 | Dagster agent / ECS service unhealthy | page | PagerDuty | **Data Platform on-call (secondary)** | `07` "who is paged"; `component-design.md` orchestrator |
| A12 | `gold_pii` accessed by a principal outside `northwind_pii_readers` | page | PagerDuty | Security on-call + DPO | `08` access control (audit) |

Routes A1-A7, A11 land on the `observability` Terraform module's SNS topic ->
PagerDuty service; warns go to Slack via AWS Chatbot. `AlertResource` in
`northwind_dagster/resources.py` carries `page()` / `warn()` (**TODO** implement
bodies).

## SLOs

| SLO | Target | Window | Metric |
|-----|--------|--------|--------|
| `gold` published + reconciled by 06:00 UTC | **99%** of days | 30 days | `publish_success` timestamp |
| zero unreconciled publishes | **100%** | always | `gate_result` == PASS on every `_SUCCESS` |
| source freshness within its SLA | **98%** per source | 30 days | `freshness_lag` vs `error_after` |
| `curated_build` within the 35-min budget | **95%** of runs | 30 days | `run_duration_s` for `curated_build` |
| monthly run cost `<= $6,000` | **100%** of months | monthly | `compute_cost_usd` sum |
| DQ pass-rate per model | **>= 99.5%** | 7-day | `dq_score` |

Targets are proposals for the go-live review - **TODO** confirm the 06:00 SLO
percentage and the error budget owner with the sponsor.

## "Healthy pipeline" definition  (restated from `09`)

All six ingest assets **fresh** for the business date, `curated_build` **green**
(models + all DQ tests), **reconcile PASS**, `gold` + `gold_pii` **published
before 06:00 UTC** with a `_SUCCESS` marker, spend **on track** (`< 80%` of the
monthly budget run-rate). Anything else = degraded; a missing `_SUCCESS` past
06:00 or a reconcile FAIL = incident.

## Wiring checklist

- [ ] every metric above has an emit point in code / dbt / IaC (table column
      "Emit point" - fill the **TODO**s: `freshness_lag`, `AlertResource` bodies)
- [ ] alert routes A1-A12 exist in the `observability` Terraform module and
      resolve to a real PagerDuty service + Slack channel
- [ ] `source_freshness` + `schema_drift` implemented as gate assets
      (`/validate-config` #15) so DQ14/DQ15 + A3/A6 can fire
- [ ] the 4 dashboards exist and are linked from `runbook.md`
- [ ] dashboards defined as code where the platform allows
- [ ] a **synthetic failure of each paging condition (A1-A5, A7, A11, A12)** has
      been fired once in dev and reached the right person - the **Failure drill**
      in `go-live-checklist.md`
- [ ] log retention set to 13 months (runs) / 5 years (`_recon`) in IaC
- [ ] `gold_pii` access audit (A12) wired to UC audit logs
