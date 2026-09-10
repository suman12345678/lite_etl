---
name: build-etl-components
description: Run Phase 3 of the ETL data-harness design process - turn the Phase 2 design into a build plan, per-component buildsheets, a dbt project scaffold, a fixtures catalog and a local-dev guide, and scaffold a starter repo tree (dbt project, extractor stubs, unit tests) under the active project workspace's build/ folder. Use after the architecture design is done, or when the user runs "/build-components".
---

# build-etl-components  (Phase 3)

Turn the design into something a developer can build against: an ordered build
plan, a concrete spec per component, and a scaffolded starter repo. This skill
plans and scaffolds; it does not deliver a running pipeline (that is Phases 4-5)
and it does not execute anything.

## Step 0 - Resolve the workspace and check preconditions

1. Read `state/active-workspace` (harness root) -> `<WS>`. If missing or
   `<WS>/project.json` is absent, tell the user to run `/etl-new-project` and stop.
2. Read `<WS>/progress.json`. If `phases.2_architecture.status` is not
   `complete` (or at least `in_progress` with real content), stop and tell the
   user to run `/design-architecture` first.
3. Read every file in `<WS>/design/` - this is your entire input. Pay attention
   to `architecture-overview.md` (component inventory), `component-design.md`,
   `transformation-design.md`, `deployment-and-iac.md`, `data-entity-diagram.md`,
   `pipeline-blueprint.md`. Also skim `<WS>/requirements/` for source quirks (01)
   and DQ rules (04).
4. Skim the harness `build/templates/` for the shape of each deliverable.
5. `mkdir -p <WS>/build/` and `<WS>/build/repo/`.

## Step 1 - Decide the build shape

- **Component list & order** - from the design's component inventory; lowest
  dependency first (state/config -> secrets -> extractors -> landing ->
  dbt/transform -> DQ -> reconciliation -> loader/publish -> lineage ->
  observability). Drop anything out of scope in the brief.
- **Repo language & layout** - from `10-platform-and-deployment.md` (mono-repo vs
  split; `dbt/ extractors/ <orchestrator>/ infra/` per the design). Phase 3 fills
  `dbt/`, `extractors/`, `tests/`; Phase 4 adds `infra/` and the orchestrator.
- **Local-test strategy** - `dbt-duckdb` for the transform layer; mock
  servers / sample files / a containerised engine for sources. No cloud.
- **Fixtures** - one per source quirk in `01` and per DQ routing outcome in `04`.

## Step 2 - Write the deliverables

Write to `<WS>/build/`, from the matching harness templates:

| File | What it contains |
|------|------------------|
| `build-plan.md` | Build order table, definition of "component complete", local-run summary, the CI hook handed to Phase 4, open items. |
| `component-buildsheet-<slug>.md` (one per component) | Design refs, files to create (real paths under `build/repo/`), public interface, config keys, key logic steps, the unit-test table, fixtures needed, done checklist. |
| `dbt-project-scaffold.md` | The dbt tree to create and the model/test/snapshot/seed -> design-section map; macros to isolate engine-specific SQL; run targets; CI fixtures. (Non-dbt: the equivalent transform-module scaffold.) |
| `fixtures-catalog.md` | Per source: sample, empty, late-data, duplicate, schema-drift, bad-rows, partial fixtures; golden outputs; the shared reconciliation fixtures. |
| `local-dev.md` | Prereqs, task-runner targets, how each source is faked locally, the dev loop. |
| `README.md` | Index + one-line status + date. |

Then **scaffold the starter repo** under `<WS>/build/repo/`:

- Directory tree matching `10-platform-and-deployment.md` (at least `dbt/`,
  `extractors/`, `tests/unit/`, `tests/fixtures/`, `tests/golden/`).
- `dbt/` - `dbt_project.yml`, `packages.yml`, `profiles/profiles.yml` (with a
  `ci` DuckDB target), and **stub** model/snapshot/seed files: each stub has the
  correct name, a header comment citing its design ref, a `config()` block, and a
  `TODO` for the SQL body. `_sources.yml` / `_models.yml` skeletons with the
  known columns and the tests named in `04`.
- `extractors/` - one stub module per source with the buildsheet's function
  signature, config-key constants, docstring, and `raise NotImplementedError`.
- `tests/unit/` - one stub test file per component with the test names from the
  buildsheet, each `@skip("TODO")`.
- `tests/fixtures/` - create the fixture files named in `fixtures-catalog.md`
  with tiny synthetic rows (**no PII, no real data**).
- A task-runner file (`Makefile` / `justfile` / `noxfile.py`) with the targets in
  `local-dev.md`, and a `README.md` in `build/repo/` pointing back to
  `../build-plan.md`.

Stubs only - correct structure, names, interfaces, config seams, `TODO`s. Never
invent business logic, credentials, hostnames, or volumes.

You may run the `component-builder` subagent for the bulk scaffolding: pass it
`<WS>` and the component list. Review what it writes before closing out.

## Step 3 - Review with the user

Present: the build order, the repo tree you scaffolded, the per-component
interfaces, and the fixtures list. Ask for corrections (naming, order, extra
components, language). Revise.

## Step 4 - Close out

Update `<WS>/progress.json`: `phases.3_build_and_test.status`,
`deliverables` = filenames written (list the `.md` files; note the repo scaffold
path), `updated` = today, append a `history` entry. Set `active_phase` to
`4_pipeline_and_git`. Tell the user Phase 4 (`/assemble-pipeline`) is next.

## Guardrails

- Scaffold, don't implement. Every file is a skeleton with `TODO`s.
- No secrets, hostnames, credentials, or real data anywhere - `config.example.*`
  only, referenced by env var / secret path.
- Every component file traces to a `design/` element; do not add components the
  design does not name.
- Never write outside `<WS>/` except to read harness templates.
