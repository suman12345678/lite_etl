# hardening/ (harness) - Phase 5 templates shared across all projects

This folder holds the **reusable** Phase 5 (Full testing & hardening) templates.
It is part of the harness, not part of any one project.

| Item | Purpose |
|------|---------|
| `templates/` | Blank shapes for each Phase 5 deliverable. The `harden-etl-pipeline` skill copies these into a project's `hardening/` folder and fills them. |

## What Phase 5 produces (into `<workspace>/hardening/`)

| File | Contents |
|------|----------|
| `test-strategy.md` | The test pyramid for this pipeline (unit / integration / contract / end-to-end / data), coverage targets, where each runs, what gates merge vs deploy. |
| `dq-behaviour-matrix.md` | Every DQ rule x input scenario -> expected routing (pass / warn / quarantine / fail). Turns `requirements/04` into executable cases. |
| `reconciliation-fixtures.md` | Per reconciliation check: a PASS fixture, a FAIL fixture, a tolerance-boundary fixture, and the expected gate behaviour. |
| `integration-e2e-plan.md` | Integration + end-to-end + contract test scenarios: what is stubbed vs real, the golden business date, backfill and replay scenarios. |
| `ci-gates.md` | The merge and deploy gates: what must be green, branch protection, promotion gates, security/IaC scans. |
| `observability-wiring.md` | Metrics / logs / traces to emit, dashboards, alert rules mapped to `07`/`09`, SLO definitions, the "healthy pipeline" definition. |
| `security-review.md` | Checklist + findings: secrets, least privilege, PII treatment verification, encryption, network, audit, dependency/IaC scan; sign-off. |
| `runbook.md` | Operate the pipeline: normal run, common failures + fixes, backfill procedure, rollback procedure, on-call escalation. |
| `go-live-checklist.md` | Cutover steps, drills to pass (backfill / rollback / failover), sign-offs, the go-live rollback plan. |
| `README.md` | Index + one-line status + date. |

Run `/harden-pipeline` after Phase 4. See `../MAP.md`.
