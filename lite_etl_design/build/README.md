# build/ (harness) - Phase 3 templates shared across all projects

This folder holds the **reusable** Phase 3 (Build & test components) templates. It
is part of the harness, not part of any one project.

| Item | Purpose |
|------|---------|
| `templates/` | Blank shapes for each Phase 3 deliverable. The `build-etl-components` skill copies these into a project's `build/` folder and fills them, then scaffolds a starter repo tree under `<workspace>/build/repo/`. |

## What Phase 3 produces (into `<workspace>/build/`)

| File | Contents |
|------|----------|
| `build-plan.md` | Component build order, per-component done-criteria, how to run each locally, definition of "component complete", CI hook. |
| `component-buildsheet.md` (one per component) | Per component: design refs, files to create, public interface, config keys, unit tests to write, fixtures needed, failure-mode tests, done checklist. |
| `dbt-project-scaffold.md` | The concrete dbt project tree to create and which model / test / snapshot / seed maps to which Phase 2 design section (for non-dbt: the transform-module scaffold). |
| `fixtures-catalog.md` | Per source: sample-data fixtures, golden outputs, edge-case fixtures (late data, dupes, schema drift, nulls). |
| `local-dev.md` | How to run each component locally (DuckDB for dbt, mocked APIs, sample files), task runner targets, dependency list. |
| `README.md` | Index + one-line status + date. |
| `repo/` | Scaffolded starter tree - real directory layout, config skeletons, and stub files with `TODO` markers, derived from the Phase 2 design. Not working code; a skeleton to fill. |

Run `/build-components` after Phase 2 is done. See `../MAP.md` for the full flow.
