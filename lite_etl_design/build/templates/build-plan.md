# Build plan

> Phase 3 deliverable. Written by `build-etl-components` from the workspace's
> `design/` folder. The order components are built, what "done" means for each,
> and how to run them locally.

- **Project:**
- **Date / version:**
- **Design baseline:** (which `design/` files + version this is built on)
- **Repo location:** `<workspace>/build/repo/` (scaffold) -> promoted to the real
  repo in Phase 4

## 1. Build order

Build one component at a time, lowest dependency first. Each must pass its unit
tests against fixtures before the next starts.

| # | Component | Depends on | Design ref | Buildsheet |
|---|-----------|-----------|-----------|-----------|
| 1 | State store / config loader | - | component-design | `component-buildsheet-statestore.md` |
| 2 | Secrets resolver | 1 | component-design; 08 | ... |
| 3 | Extractor: `<source>` (repeat per source) | 1, 2 | component-design; 01 | ... |
| 4 | Landing writer | 3 | component-design; 02 | ... |
| 5 | dbt project (staging -> intermediate -> marts + snapshots + seeds) | 4 | transformation-design | `dbt-project-scaffold.md` |
| 6 | DQ engine / dbt test wiring | 5 | transformation-design; 04 | ... |
| 7 | Reconciliation engine | 5, 6 | component-design; 05 | ... |
| 8 | Loader / publisher | 7 | component-design; 02 | ... |
| 9 | Lineage / metadata emitter | 4, 5 | component-design; 06 | ... |
| 10 | Observability hooks | all | component-design; 09 | ... |

(Adjust to the component inventory in `design/architecture-overview.md`. Drop
rows for anything out of scope.)

## 2. Definition of "component complete"

A component is done when **all** hold:

- [ ] Code exists in `build/repo/` at the path in its buildsheet.
- [ ] Public interface matches the buildsheet (inputs, outputs, config keys).
- [ ] Unit tests cover: happy path, each documented failure mode, idempotent
      re-run, and every edge case in `fixtures-catalog.md` for its source.
- [ ] Runs locally per `local-dev.md` with no cloud dependency (mocks / DuckDB /
      sample files).
- [ ] Emits the metrics + lineage events named in the design.
- [ ] Config-driven - no hard-coded hostnames, paths, or credentials.
- [ ] Added to the local test runner target and the CI unit-test job.

## 3. Local run

- **Prereqs:** _language runtime, dbt + adapter (+ `dbt-duckdb` for tests), task
  runner_
- **One-liner per component:** see `local-dev.md`
- **Full local pass:** `<task runner> test` runs every component's unit tests +
  `dbt build` against DuckDB with fixtures. Must be green before Phase 4.

## 4. CI hook (handed to Phase 4)

- Unit tests + `dbt build --target ci` on every push.
- Lint (`sqlfluff`, formatter, `terraform fmt` when infra lands in Phase 4).
- Coverage threshold: _e.g. 80% on extract/transform/recon logic._

## 5. Open items

| # | Item | Blocks which component | Owner |
|---|------|------------------------|-------|
| | | | |
