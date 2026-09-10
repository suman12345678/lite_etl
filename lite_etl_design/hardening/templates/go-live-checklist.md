# Go-live checklist

> Phase 5 deliverable. Everything that must be true before the pipeline runs
> production loads, the drills it must pass, and the plan if go-live itself goes
> wrong.

- **Project:**  - **Target go-live date:**  - **Owner:**

## Readiness

| # | Item | Evidence | Status |
|---|------|----------|--------|
| 1 | All Phase 3 unit tests green in CI | CI run link | |
| 2 | Integration + E2E suites green on `main` (nightly) | run link | |
| 3 | DQ behaviour matrix fully implemented + passing | `dq-behaviour-matrix.md` | |
| 4 | Reconciliation fixtures (PASS/FAIL/boundary) passing per check | `reconciliation-fixtures.md` | |
| 5 | CI gates enforced on `main` (branch protection on) | repo settings | |
| 6 | Terraform applied to prod; drift plan empty | apply + plan links | |
| 7 | Observability: dashboards live, every paging alert fired once in dev | `observability-wiring.md` | |
| 8 | Security review signed off; high/critical findings closed | `security-review.md` | |
| 9 | Runbook reviewed by the on-call team | `runbook.md` | |
| 10 | Historical backfill completed + reconciled for the required look-back | backfill report | |
| 11 | Consumers notified of cutover + `gold` contract | comms link | |
| 12 | Secrets provisioned + rotation scheduled in prod | secret manager | |

## Drills to pass (in a non-prod env)

| Drill | Pass criteria |
|-------|---------------|
| Backfill drill | re-run N past business dates oldest-first; each reconciles; final state correct |
| Rollback drill | publish a bad day (gate bypassed in test), run the runbook rollback; `gold` restored, timing recorded |
| Failure drill | trigger each paging condition; correct alert reaches the right person |
| DR / failover drill | restore from backup / promote standby within RTO; data loss within RPO (`09`) |

## Cutover steps

1. Freeze source-side changes for the window.
2. Final backfill / catch-up to `T-1`.
3. Enable prod schedules; disable any legacy job feeding the same targets.
4. Watch the first `<n>` production runs to green + reconciled.
5. Confirm consumers see `gold`; close the cutover.

## Go-live rollback plan

- Trigger: first prod run fails reconciliation, or a consumer-blocking defect.
- Action: disable prod schedules; consumers fall back to `<legacy source>`;
  keep `bronze` landing (no data lost); fix forward; re-attempt next window.
- Decision owner: `<name/role>`. Communicate on `<channel>`.

## Sign-off

| Role | Name | Date |
|------|------|------|
| Data owner | | |
| Platform / on-call lead | | |
| Security | | |
| Sponsor | | |
