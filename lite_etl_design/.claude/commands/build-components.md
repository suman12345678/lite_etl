---
description: Phase 3 - turn the architecture design into a build plan, per-component buildsheets and a scaffolded starter repo
argument-hint: [optional focus, e.g. "start with the Shopify extractor" or "Python + uv"]
---

Start (or resume) **Phase 3 - Build & test components** of the ETL data-harness
design.

Invoke the `build-etl-components` skill and follow it exactly:

1. Resolve the active workspace `<WS>` from `state/active-workspace` (stop if none).
2. Confirm Phase 2 is done - read `<WS>/progress.json` and every file in
   `<WS>/design/`. If the design is missing, stop and tell me to run
   `/design-architecture`.
3. Decide the component build order (lowest dependency first), the repo language
   and layout (from `10-platform-and-deployment.md`), and the local-test
   strategy (DuckDB for dbt, mocks / sample files for sources - no cloud).
4. Write to `<WS>/build/`: `build-plan.md`, one `component-buildsheet-<slug>.md`
   per component, `dbt-project-scaffold.md`, `fixtures-catalog.md`,
   `local-dev.md`, `README.md`. Templates come from the harness `build/templates/`.
5. Scaffold the starter repo under `<WS>/build/repo/` - directory tree, dbt
   project with stub models / snapshots / seeds / `_sources.yml`, extractor
   stubs with real signatures, unit-test stubs, tiny synthetic fixtures, a
   task-runner file. Stubs and `TODO`s only - **except the walking-skeleton
   slice** (`demo/`, `DEMO.md`, a working `tests/conftest.py`, real fixtures for
   one source + its bad-row/fixed pair + control totals, `<task> demo` /
   `demo-fail` targets), which gets real small bodies and must run on DuckDB.
   See `build/templates/demo-harness.md`.
6. Run the Step 2.9 self-check (compile / YAML / `dbt parse` / `<task> demo` /
   `pytest tests/unit/test_demo.py`) and report the result.
7. Walk me through the build order, the tree, the component interfaces and the
   demo run; revise on feedback.
8. Update `<WS>/progress.json` (phase 3 status, deliverables, `active_phase` ->
   `4_pipeline_and_git`).

Optional heavy lifting: run the `component-builder` subagent (pass it `<WS>`) to
draft the buildsheets + scaffold, then review and land them.

Focus note, if any: $ARGUMENTS
