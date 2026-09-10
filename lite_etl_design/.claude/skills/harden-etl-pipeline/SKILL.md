---
name: harden-etl-pipeline
description: Run Phase 5 of the ETL data-harness design process - turn the built pipeline into a tested, operable, production-ready one: a test strategy, a DQ behaviour matrix, reconciliation fixtures, an integration/e2e plan, CI gates, observability wiring, a security review, a runbook and a go-live checklist, written to the active project workspace's hardening/ folder. Use after the pipeline is assembled, or when the user runs "/harden-pipeline".
---

# harden-etl-pipeline  (Phase 5)

Take the assembled pipeline and make it production-ready on paper and in test:
full test coverage, executable DQ and reconciliation specs, CI gates,
observability, a security review, a runbook, and a go-live checklist with drills.
This skill plans and specifies; it does not run tests, deploy, or go live.

## Step 0 - Resolve the workspace and check preconditions

1. Read `state/active-workspace` -> `<WS>`. If missing or `<WS>/project.json` is
   absent, tell the user to run `/etl-new-project` and stop.
2. Read `<WS>/progress.json`. If `phases.4_pipeline_and_git.status` is not
   `complete` (or `in_progress` with real content), stop and tell the user to run
   `/assemble-pipeline` first.
3. Read `<WS>/requirements/` (especially `04`, `05`, `07`, `08`, `09`),
   `<WS>/design/`, `<WS>/build/`, `<WS>/pipeline/`. List `<WS>/build/repo/`.
4. Skim the harness `hardening/templates/`.
5. `mkdir -p <WS>/hardening/`.

## Step 1 - Settle the hardening choices

- **Test pyramid** - which layers, tooling, where each runs, what gates merge vs
  deploy vs promote. Unit tests already exist (Phase 3); add integration,
  contract, e2e, data.
- **DQ behaviour** - every rule in `04` -> scenarios -> routing (pass / warn /
  quarantine / fail) + threshold cases.
- **Reconciliation fixtures** - PASS / FAIL / boundary per check in `05`, and the
  exact gate action each must produce.
- **CI gates** - the merge / deploy / promote gate contents, branch protection,
  security + IaC scans.
- **Observability** - the metric set, dashboards, alert rules mapped to `07`/`09`,
  SLOs, the healthy definition.
- **Security review** - walk `08` against the build; record findings.
- **Runbook + go-live** - operational procedures, the drills, the cutover and its
  rollback plan.

Anything the earlier phases left open becomes a `TODO` with a pointer.

## Step 2 - Write the deliverables

Write to `<WS>/hardening/`, from the matching harness templates:

| File | What it contains |
|------|------------------|
| `test-strategy.md` | The pyramid, coverage targets, test environments, test data rules, what is not tested. |
| `dq-behaviour-matrix.md` | Every `04` rule x input scenario -> expected routing + threshold cases + reporting assertions. |
| `reconciliation-fixtures.md` | Per `05` check: PASS / FAIL / boundary fixtures, expected verdict + gate action, report + replay assertions. |
| `integration-e2e-plan.md` | Integration + contract + e2e scenarios, stubbed-vs-real matrix, runtime budget. |
| `ci-gates.md` | Merge / deploy / promote gates, branch protection, nightly suite, what a failing gate does. |
| `observability-wiring.md` | Metrics, logs, dashboards, alert rules, SLOs, healthy definition, wiring checklist. |
| `security-review.md` | The `08` checklist walked against the build, findings table, sign-off. |
| `runbook.md` | Normal day, common failures + fixes, backfill procedure, rollback procedure, escalation. |
| `go-live-checklist.md` | Readiness items, the drills, cutover steps, the go-live rollback plan, sign-offs. |
| `README.md` | Index + one-line status + date. |

You may run the `hardening-planner` subagent for the bulk drafting: pass it
`<WS>`. Review before closing out.

## Step 3 - Review with the user

Present: the test pyramid and what gates what, the DQ matrix and reconciliation
fixtures at a glance, the alert table, the security findings, and the go-live
drills. Ask for corrections. Revise.

## Step 4 - Close out

Update `<WS>/progress.json`: `phases.5_full_testing_and_hardening.status`,
`deliverables`, `updated`, a `history` entry. If all five phases are `complete`,
say so and point at the go-live checklist as the handoff artefact. Note that
actually running the suites, wiring the alerts, and going live are human steps
outside this harness.

## Guardrails

- Specify and plan only - never run tests, deploy, or execute drills.
- Every test / gate / alert traces to a requirement or design element.
- No secret values, account ids, or real data in any fixture or example.
- Never write outside `<WS>/` except to read harness templates.
