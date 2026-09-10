# Runbook

> Phase 5 deliverable. How to operate the pipeline day to day and in an
> incident. Written for whoever is on-call.

- **Project:**  - **On-call rota / escalation:** (from `07`)
- **Dashboards:** (links from `observability-wiring.md`)
- **Repo / orchestrator / warehouse consoles:** (links)

## Normal day

- Schedule: `<pipelines and times>`; SLA: `<gold ready by ...>`.
- Where to look: pipeline-health dashboard; expected green by `<time>`.
- The daily gate: reconciliation PASS -> publish -> watermark advance.

## Common failures

| Symptom | Likely cause | Check | Fix |
|---------|--------------|-------|-----|
| extract task failing | source down / creds expired / rate limit | task logs, source status | retry after fix; rotate secret; back off |
| file missing past deadline | upstream delivery late | inbound bucket / SFTP | wait per policy; escalate to source owner; do NOT force publish |
| schema drift halt | source added/removed/retyped a column | drift report vs `sources.yml` | update the source contract via PR; re-run |
| DQ over threshold | bad source data / rule too tight | reject table + `_dq_rule` | triage rows; fix source or tune rule via PR; re-run |
| reconciliation FAIL | real data break / late data / control report wrong | `_reconciliation.json` (check, delta, partition) | find the break; re-extract window; do NOT publish until PASS |
| pipeline slow / SLA risk | volume spike / small cluster / lock contention | duration metric, warehouse load | scale compute for the run; investigate after |
| deploy canary red | bad merge | canary logs, last PR | roll back to previous SHA (below) |

## Backfill procedure

1. Identify the `[from, to]` business-date window.
2. Run: `<backfill command / params>` - one `run_id` per date, oldest first.
3. Each date must reconcile PASS before the next; watermark untouched until then.
4. For large windows: scale compute, run off-peak, then resume the normal schedule.
5. Verify: row counts + control totals per backfilled date; spot-check `gold`.

## Rollback procedure

| Case | Steps |
|------|-------|
| bad dbt model | revert the PR; redeploy previous SHA; `dbt build --full-refresh --select <affected>+ --target <env>`; re-reconcile |
| bad infra change | `terraform apply` the previous SHA in `infra/envs/<env>` |
| bad publish already consumed | warehouse time-travel / `RESTORE` the affected tables to the last-good version; rebuild the business date; notify consumers |
| whole env unhealthy | promote the standby / last-good; freeze deploys; incident review |

## Escalation

1. On-call primary (page).  2. Secondary after `<n>` min.  3. Data platform lead.
4. Source system owner for source-side issues.  Incident channel: `<link>`.

## Contacts & references

| What | Where |
|------|-------|
| architecture | `design/architecture-overview.md` |
| pipeline DAGs | `design/pipeline-blueprint.md` |
| reconciliation spec | `requirements/05-reconciliation.md` |
| security / PII | `requirements/08-security-and-compliance.md` |
