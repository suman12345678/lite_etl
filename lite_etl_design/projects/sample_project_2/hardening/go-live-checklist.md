# Go-live checklist - Northwind Commerce (DEMO)

> Phase 5 deliverable. Everything that must be true before `northwind_daily` runs
> production loads, the drills it must pass, and the plan if go-live itself goes
> wrong. This is the **handoff artefact** for the harness.

- **Project:** Northwind Commerce - Unified Retail Analytics Harness
- **Target go-live:** MVP (OLTP + Shopify + POS -> `gold` sales) end Q4; all 6
  sources Q1 next year (`00` milestones)
- **Owner:** _(TODO - Analytics Eng lead)_

## Readiness

| # | Item | Evidence | Status |
|---|------|----------|--------|
| 1 | All Phase 3 unit tests implemented + green in CI; coverage `>= 80%` on `extractors/ recon/ publish/` | `pr.yml:unit` run link; `--cov-fail-under=80` set | ☐ |
| 2 | Data + contract tests green; DQ behaviour matrix fully implemented | `dq-behaviour-matrix.md` rows all have a passing test | ☐ |
| 3 | Reconciliation fixtures (PASS / FAIL / boundary) passing for **all 8** checks | `reconciliation-fixtures.md`; `tests/fixtures/recon/` | ☐ |
| 4 | Integration (I1-I7) + E2E (E1-E8) green on `main` nightly for 5 consecutive nights | nightly run links | ☐ |
| 5 | CI gates enforced on `main` - branch protection on, required checks incl. `contract`, `integration`, `iac-scan` | repo settings screenshot | ☐ |
| 6 | `source_freshness` + `schema_drift` implemented as gate assets (`/validate-config` #15) | `northwind_dagster/assets/` | ☐ |
| 7 | **Security review signed off** - F1 + F2 (High) closed; F3-F9 closed or accepted with rationale | `security-review.md` sign-off | ☐ |
| 8 | `gold_pii` UC row filter + column mask live; `northwind_pii_readers` = the 5 named people; commercial-field column masks on `gold` (F1) | UC policy + a masked-read test | ☐ |
| 9 | Databricks secret scopes + ACLs in Terraform; all prod secrets provisioned; rotation scheduled (F2; `08`) | `infra/` + Secrets Manager | ☐ |
| 10 | Terraform applied to **prd**; `drift.yml` plan empty for dev/stg/prd | apply + plan links | ☐ |
| 11 | Observability: 4 dashboards live; every paging alert (A1-A5, A7, A11, A12) fired once in dev and reached the right person | `observability-wiring.md` checklist | ☐ |
| 12 | Retention/lifecycle set per `08` per zone; `gold_pii` 25-month deletion job scheduled (F6) | `infra/` lifecycle + the job | ☐ |
| 13 | RTBF: `scripts/rtbf.py` + runbook section exist; RTBF drill passed (F7) | drill record | ☐ |
| 14 | Historical backfill completed + reconciled for the required look-back (24 months, `00`/Q2) | backfill report - row counts + control totals per date | ☐ |
| 15 | Runbook reviewed by the on-call team; escalation contacts + channel links filled | `runbook.md` review note | ☐ |
| 16 | Consumers (Looker, Braze, Finance close) notified of cutover date + the `gold` contract (C2/C3) | comms link | ☐ |
| 17 | Dagster Cloud new-SaaS security review complete **or** `mode = oss_selfhost` chosen (`09` / Q3) | review record / `orchestrator_mode` in `*.tfvars` | ☐ |
| 18 | Wholesale revenue-recognition grain confirmed by Finance (Q4); `fct_wholesale_opportunity` + recon R2 wholesale row updated | Finance sign-off | ☐ |

## Drills to pass  (in dev / stg - never prod)

| Drill | Steps | Pass criteria |
|-------|-------|---------------|
| **Backfill drill** | `dagster job backfill` 3 past business dates, oldest-first, over `ingest` then `curated_build` (E6) | all 3 reconcile independently; `<= 3` concurrent; each watermark advances only on its own PASS; final `_state.watermarks` correct; `gold` spot-check clean |
| **Rollback drill** | publish a deliberately bad `D` with the recon gate bypassed (test hook), then run the `runbook.md` "bad publish already consumed" steps (E7) | `RESTORE ... VERSION AS OF` restores `gold` + `gold_pii`; `D` rebuilds clean and reconciles; **time from detection to restored recorded** (target < RTO 4h) |
| **Failure drill** | trigger each paging condition A1-A5, A7, A11, A12 with a synthetic fault | the correct alert reaches the correct person/rota within 5 min; no false extras; Slack warns (A6, A8-A10) land in the right channel |
| **RTBF drill** | run `scripts/rtbf.py` for a synthetic subject in stg (F7) | per-subject salt dropped; `gold_pii` rows + inbound files deleted; `dim_customer` tombstoned (`is_erased`, attrs null, `customer_sk` kept); the subject's `email_hash` can no longer be re-derived; `fct_order` totals still balance; completed inside a simulated 30-day SLA |
| **DR / failover drill** | promote the weekly `eu-west-2` `gold` + `gold_pii` deep clone **read-only**; simulate primary-region loss | consumers can read from the clone within **RTO 4h**; data loss within **RPO 24h**; documented steps match reality |
| **Peak-load drill** | run the 5x Black-Friday golden day on a `prd`-sized job cluster in dev (E8) | `curated_build` < 35 min; each ingest < 20 min; recon PASS; run cost within budget share; photon confirmed on `curated_build` |

## Cutover steps

1. Freeze source-side schema changes for the cutover window; notify source owners.
2. Final backfill / catch-up to `T-1` (24-month history reconciled per item 14).
3. Provision + verify prod secrets; confirm rotation schedules are set.
4. Enable prod Dagster schedules + the `pos_s3_sensor`; disable any legacy job
   feeding the same `gold` targets.
5. Watch the first **3** production runs to green + reconciled + `_SUCCESS`
   before 06:00; on-call actively monitoring each.
6. Confirm Looker (06:30 refresh), Braze and Finance-close consumers see `gold`;
   run contract checks C2/C3 against prod.
7. Close the cutover; announce on `#northwind-data`; start the 2-week hypercare.

## Go-live rollback plan

- **Trigger:** the first prod run fails reconciliation and cannot be fixed inside
  the window, or a consumer-blocking defect in `gold`.
- **Action:** disable the prod Dagster schedules + sensor; consumers fall back to
  the legacy source for the affected day; **`bronze` landing keeps running** (no
  raw data lost - RPO 24h holds); fix forward on a branch; re-attempt the next
  daily window.
- **Do NOT** attempt an in-place hotfix on prod without a PR + the 2 prd
  approvers unless it is a `hotfix`-labelled change.
- **Decision owner:** Analytics Eng lead (data), Data Platform lead (infra).
  Communicate on `#northwind-incident`.

## Sign-off

| Role | Name | Date |
|------|------|------|
| Data owner (Analytics Eng lead) | | |
| Platform / on-call lead | | |
| Security | | |
| DPO (PII + RTBF) | | |
| Sponsor | | |

---

_Running the suites, wiring the alerts, executing the drills and the cutover
itself are human steps outside this harness._
