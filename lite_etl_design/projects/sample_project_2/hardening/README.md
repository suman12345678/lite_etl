# Phase 5 - Full testing & hardening - Northwind Commerce (DEMO)

> Index of the Phase 5 deliverables. Takes the assembled pipeline
> ([`../pipeline/`](../pipeline/)) and the built components
> ([`../build/`](../build/)) and specifies what makes it production-ready:
> the test pyramid, executable DQ + reconciliation specs, CI gates,
> observability + SLOs, a security review, a runbook, and a go-live checklist
> with drills. **Specifies and plans only** - no tests run, nothing deployed,
> no drills executed.

- **Project:** Northwind Commerce - Unified Retail Analytics Harness
- **Date / version:** 2026-09-09 / v1.0
- **Status:** drafted, pending review. On sign-off -> `go-live-checklist.md` is the handoff artefact.

## Files

| File | What it contains |
|------|------------------|
| [`test-strategy.md`](test-strategy.md) | The pyramid (unit / data / integration / contract / e2e), coverage targets, test environments, test-data rules, out-of-scope. |
| [`dq-behaviour-matrix.md`](dq-behaviour-matrix.md) | Every `requirements/04` rule x input scenario -> routing (pass / warn / quarantine / fail), threshold cases, reporting assertions. |
| [`reconciliation-fixtures.md`](reconciliation-fixtures.md) | Per `requirements/05` check: PASS / FAIL / boundary fixtures, expected verdict + gate action, `_reconciliation.json` + replay assertions. |
| [`integration-e2e-plan.md`](integration-e2e-plan.md) | Integration (I1-I7), contract (C1-C4) and end-to-end (E1-E8) scenarios, stubbed-vs-real matrix, runtime budget. |
| [`ci-gates.md`](ci-gates.md) | Merge / deploy / promote gate contents, branch protection, the nightly suite, what a failing gate does. |
| [`observability-wiring.md`](observability-wiring.md) | Metric set, logs, 4 dashboards, the alert table mapped to `07`/`09`, SLOs, "healthy" definition, wiring checklist. |
| [`security-review.md`](security-review.md) | `requirements/08` walked against the build; findings table (F1-F8); sign-off block. |
| [`runbook.md`](runbook.md) | Normal day, common failures + fixes, backfill procedure, rollback procedures, escalation. |
| [`go-live-checklist.md`](go-live-checklist.md) | 14 readiness items, 4 drills, cutover steps, the go-live rollback plan, sign-offs. |

## Carried in from Phase 4 `/validate-config`

| Gap | Where it lands in Phase 5 |
|-----|---------------------------|
| Databricks secret scopes + ACLs not scaffolded (`iac-plan.md` #5) | `security-review.md` finding **F2**; `go-live-checklist.md` item 12 |
| `source_freshness` / `schema_drift` assets are TODO comments, not stubs (`orchestration-wiring.md` #15) | `dq-behaviour-matrix.md` DRIFT / FRESH rows; `integration-e2e-plan.md` C1 + E2; `security-review.md` note |

## Open items still tracked

| # | Item | Handling |
|---|------|----------|
| Q3 | Dagster Cloud vs OSS | `security-review.md` supply-chain row: new-SaaS review of Dagster Cloud is a go-live blocker if `mode=cloud_agent`. |
| Q2 | Backfill depth 12 vs 24 months (`00` says 24) | `go-live-checklist.md` item 10 + Backfill drill; runtime only. |
| Q4 | Wholesale revenue-recognition grain | `dq-behaviour-matrix.md` + `reconciliation-fixtures.md` wholesale GMV rows carry a `TODO` until Finance confirms. |

Running the suites, wiring the alerts, executing the drills and going live are
**human steps outside this harness.**
