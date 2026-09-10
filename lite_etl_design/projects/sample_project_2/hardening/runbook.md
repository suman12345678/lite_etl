# Runbook - Northwind Commerce (DEMO)

> Phase 5 deliverable. How to operate `northwind_daily` day to day and in an
> incident. Written for whoever is on-call.

- **Project:** Northwind Commerce - Unified Retail Analytics Harness
- **On-call rota / escalation (`07`):** Analytics Eng on-call = **primary**;
  Data Platform on-call = **secondary** (agent / infra / network).
- **Dashboards (`observability-wiring.md`):** Pipeline health (Dagster UI +
  Databricks SQL) · Data quality (Elementary) · Cost · Freshness _(TODO paste links)_
- **Consoles:** Dagster `northwind-<env>` · Databricks `northwind-<env>` workspace
  · GitHub `northwind/northwind-data` · AWS `northwind-<env>` account _(TODO links)_
- **Incident channel:** `#northwind-incident` _(TODO)_ · status page _(TODO)_

## Normal day (UTC)

| Time | What should be happening |
|------|--------------------------|
| 00:00-04:00 | `oltp_ingest` every 4h; `shopify_ingest` hourly; `salesforce_ingest` every 6h; POS files arrive 02:00-03:30 and the `pos_s3_sensor` fires |
| 04:00 | `pos_ingest` sweep backstop; `ga4_ingest` (D-2 shard) |
| 05:00 | `fx_ingest`; all ingests should be **fresh for D** |
| 05:15 | `curated_build` starts (dbt silver+gold + tests + snapshots) |
| ~05:50 | `reconcile` asset check (the 8 checks in `reconciliation-fixtures.md`) |
| 05:55-06:00 | `publish` -> `catalog_register` (`_SUCCESS`) -> `advance_watermarks` -> `emit_metrics` |
| 06:00 | **SLA: `gold` + `gold_pii` published and reconciled.** 06:30 Looker refresh consumes it. |

**The daily gate:** `reconcile` **PASS** -> `publish` -> `_SUCCESS` -> watermark
advance. No `_SUCCESS` past 06:00 = incident (alert **A7**).

**Where to look first:** the Pipeline-health dashboard - asset status for today's
`D`, the SLA countdown, and the last `gate_result`.

## Common failures

| Symptom (alert) | Likely cause | Check | Fix |
|-----------------|--------------|-------|-----|
| extract task failing (**A1**) | source down / creds expired / rate limit | Dagster asset logs; source status page; `secret-scope` age | let the 3 retries run; if creds: rotate the secret in Secrets Manager, re-run the asset; if rate-limit: it backs off - re-run after the window |
| POS file missing past 04:30 (**A2**) | store upload late / POS vendor issue | `s3://northwind-<env>-inbound/pos/dt=<D>/` - which `store=` is missing | wait per policy; escalate to the POS source owner; **do NOT force publish** - a missing store fails recon R2 anyway |
| schema drift halt (**A3**) | source added / removed / retyped a column | the drift report vs `dbt/models/staging/<src>/_<src>__sources.yml` | update the source contract via a PR (`sources.yml` + affected `stg_` model), get it reviewed, merge, re-run `D` |
| DQ over threshold (**A4**) | bad source data, or a rule too tight | `reject__<entity>` for `D` - `reason_code`, `_dq_rule`; the Elementary DQ dashboard | triage the rows; fix at source (raise with the owner) or tune the rule via a PR; re-run `curated_build` for `D` |
| reconciliation FAIL (**A5**) | real data break / late data / a wrong control report | `_reconciliation.json` at `_recon/dt=<D>/` - which `check`, `channel`, `delta`, `key_sample` | find the break (see per-check notes below); re-extract the affected window; **do NOT publish until PASS** |
| `curated_build` not done by 05:45 (**A6**, warn) | volume spike / small cluster / lock contention | `run_duration_s` for `curated_build`; Databricks job cluster load | let it finish if it will still make 06:00; if not, scale the job cluster for this run and re-trigger; investigate after |
| SLA breach - no `_SUCCESS` by 06:00 (**A7**) | any of the above unresolved | Pipeline-health dashboard; the open page | work the underlying alert; notify `#northwind-data` that `gold` for `D` is late; consumers see **yesterday's** data, not wrong data |
| Dagster agent / ECS unhealthy (**A11**) | ECS task crash / AZ issue / Dagster Cloud outage | ECS service events; Dagster Cloud status | **secondary (Data Platform) on-call** owns this; runs queue and resume on recovery; backfill any missed `D` |
| `gold_pii` accessed by a non-reader (**A12**) | mis-grant / break-glass misuse | UC audit log; `northwind_pii_readers` membership | revoke; confirm with DPO; file a security incident |
| deploy canary red | bad merge to `main` | `main.yml:smoke-dev` logs; the last merged PR | `main.yml` auto-rolls back dev; if not, do the rollback below; revert the PR |

### Per reconciliation check - where the break is

| Check (`_reconciliation.json`) | First thing to look at |
|-------------------------------|------------------------|
| `row_count_identity` | the `source` named; compare `manifest.row_count` vs `bronze` vs `silver-in + rejected + superseded` - a join dropping rows, or a failed partial extract |
| `gmv_control_total` | the `channel` + `delta` sign; web -> Shopify payout export; store -> the missing `store_id` in `totals.csv`; wholesale -> SFDC closed-won amount / grain (Q4) |
| `refund_linkage` | the `refund_id` with no order - late refund vs a truly orphan refund |
| `order_equals_lines` | the `order_id` + `delta` - a line missing or a rounding bug in `to_usd` |
| `fx_coverage` | the currency + date - a new market, or a weekend with no carry-forward source |
| `duplicate_key` | the key + value - dedupe missed a case; check the `qualify_dedupe` window |
| `distribution_drift` | the metric + `%` - real spike (allowlist the date) vs a double-load or a dropped channel |
| `pii_leak` | the `schema.table.column` - a model exposing a raw field; block the deploy that introduced it |

## Backfill procedure  (`07`; `backfill.py`)

1. Identify the `[from, to]` business-date window.
2. Ingest first, oldest-first:
   `dagster job backfill --job pos_ingest_job --partition-range <from>...<to>`
   (repeat per ingest job, or backfill the `ingest` asset selection).
3. Then transform + gate over the same range:
   `dagster job backfill --job curated_build_job --partition-range <from>...<to>`.
4. **One `run_id` per date; `<= 3` concurrent; each date must `reconcile` PASS
   before its watermark advances.** A failed date stops that date only - fix and
   re-run it before it blocks nothing (later dates proceed).
5. Large windows (the 24-month go-live load, `00`/Q2): run on the `prd`
   on-demand pool over a weekend window; scale the job cluster; resume the normal
   schedule after.
6. Verify: row-count identity + GMV control totals per backfilled date;
   spot-check `gold.fct_order` for a few dates; confirm `_state.watermarks`
   landed on `<to>`.

## Rollback procedures  (`deployment-and-iac.md` s.6)

| Case | Steps |
|------|-------|
| **bad dbt model** | revert the PR; `promote.yml` (or `main.yml`) redeploys the previous SHA; `dbt build --full-refresh --select <affected>+ --target <env> --vars '{business_date: <D>}'`; re-run `reconcile` |
| **bad infra change** | `terraform apply` the previous SHA in `infra/envs/<env>` (state is versioned in S3); confirm `drift.yml` next run is empty |
| **bad publish already consumed** | `RESTORE gold.<table> TO VERSION AS OF <n>` (and `gold_pii.<table>`) via Delta time-travel to the last-good version; rebuild `D`; notify consumers on `#northwind-data` that a correction is landing |
| **whole env unhealthy** | freeze deploys; promote the last-good SHA; if data-plane loss: promote the weekly `eu-west-2` deep clone **read-only** while rebuilding (RPO 24h / RTO 4h, `09`); incident review |
| **RTBF request** (F7 - **TODO** build `scripts/rtbf.py`) | verify the request; drop the subject's per-subject salt (crypto-shred); delete their rows from `gold_pii.*` + inbound files; tombstone `dim_customer` (`is_erased=true`, attrs nulled, `customer_sk` kept); record for the next deep-clone cycle; close within the 30-day SLA |

## Escalation

1. **Analytics Eng on-call (primary)** - page.
2. **Data Platform on-call (secondary)** - after 15 min, or immediately for
   agent / ECS / network / IAM / UC-grant issues.
3. **Data Platform lead** - incident > 1h or SLA missed 2 days running.
4. **Source system owner** (`requirements/01`) - for source-side breaks.
5. **DPO + Security on-call** - any `gold_pii` exposure (**A12**) or RTBF dispute.

Incident channel: `#northwind-incident` _(TODO)_.

## Contacts & references

| What | Where |
|------|-------|
| architecture | `design/architecture-overview.md` |
| pipeline DAG + policies | `design/pipeline-blueprint.md` · `pipeline/orchestration-wiring.md` |
| reconciliation spec + fixtures | `requirements/05-reconciliation.md` · `hardening/reconciliation-fixtures.md` |
| DQ routing | `hardening/dq-behaviour-matrix.md` |
| security / PII / RTBF | `requirements/08-security-and-compliance.md` · `hardening/security-review.md` |
| alerts + SLOs | `hardening/observability-wiring.md` |
| deploy / rollback detail | `design/deployment-and-iac.md` · `pipeline/cicd-plan.md` |
