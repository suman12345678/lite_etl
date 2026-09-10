---
description: Phase 5 - turn the assembled pipeline into a tested, operable, production-ready one (test strategy, DQ matrix, recon fixtures, CI gates, observability, security review, runbook, go-live)
argument-hint: [optional focus, e.g. "emphasise the DR drill" or "we must pass SOC2"]
---

Start (or resume) **Phase 5 - Full testing & hardening** of the ETL data-harness
design.

Invoke the `harden-etl-pipeline` skill and follow it exactly:

1. Resolve the active workspace `<WS>` from `state/active-workspace` (stop if none).
2. Confirm Phase 4 is done - read `<WS>/progress.json`, `<WS>/requirements/`,
   `<WS>/design/`, `<WS>/build/`, `<WS>/pipeline/`. If the pipeline assembly is
   missing, stop and tell me to run `/assemble-pipeline`.
3. Settle the hardening choices: the test pyramid and what gates merge / deploy /
   promote; DQ behaviour per rule; reconciliation PASS/FAIL/boundary fixtures;
   CI gate contents; observability + SLOs; the security-review findings; the
   runbook and go-live drills.
4. Write to `<WS>/hardening/`: `test-strategy.md`, `dq-behaviour-matrix.md`,
   `reconciliation-fixtures.md`, `integration-e2e-plan.md`, `ci-gates.md`,
   `observability-wiring.md`, `security-review.md`, `runbook.md`,
   `go-live-checklist.md`, `README.md`. Templates come from the harness
   `hardening/templates/`.
5. Walk me through the pyramid, the DQ matrix, the reconciliation fixtures, the
   alert table, the security findings and the go-live drills; revise on feedback.
6. Update `<WS>/progress.json` (phase 5 status, deliverables). If all five phases
   are complete, say so and point at `hardening/go-live-checklist.md` as the
   handoff.

Specify and plan only - do not run tests, deploy, or execute drills.

Optional heavy lifting: run the `hardening-planner` subagent (pass it `<WS>`).

Focus note, if any: $ARGUMENTS
