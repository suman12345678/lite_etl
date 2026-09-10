---
description: Phase 2 - turn requirement files into architecture + data-flow + ER diagrams and design docs
argument-hint: [optional focus, e.g. "emphasise the reconciliation gate"]
---

Start (or resume) **Phase 2 - Architecture & Data Modeling** of the ETL
data-harness design.

Invoke the `design-etl-architecture` skill and follow it exactly:

1. Resolve the active workspace `<WS>` from `state/active-workspace` (stop if none).
2. Confirm Phase 1 is done - read `<WS>/progress.json` and every file in
   `<WS>/requirements/`. If requirements are missing, stop and tell me to run
   `/gather-requirements`.
3. Settle the load-bearing choices (ETL vs ELT, batch vs streaming, zone model,
   orchestration, storage/formats, idempotency), each traced to a requirement.
4. Write to `<WS>/design/`: `architecture-overview.md`, `architecture-diagram.md`,
   `data-flow-diagram.md`, `data-entity-diagram.md`, `component-design.md`,
   `transformation-design.md` (the dbt project blueprint), `deployment-and-iac.md`
   (Terraform module layout + the CI/CD `plan -> apply -> dbt build -> promote`
   pipeline), `pipeline-blueprint.md`, `design-decisions.md`,
   `traceability-matrix.md`, `README.md`. Diagrams as Mermaid. Templates come
   from the harness `design/templates/`.
5. Walk me through the approach, diagrams and key decisions; revise on feedback.
6. Update `<WS>/progress.json` (phase 2 status, deliverables, `active_phase` ->
   `3_build_and_test`) and tell me `/build-components` is next.

Optional heavy lifting: run the `solution-architect` subagent (pass it `<WS>`) to
draft the docs, then review and land them.

Focus note, if any: $ARGUMENTS
