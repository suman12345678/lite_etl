# Local development

> Phase 3 deliverable. How to run every component on a laptop with no cloud
> access - the loop developers and CI both use.

- **Repo:** `build/repo/`

## Prerequisites

| Tool | Version | For |
|------|---------|-----|
| `<language runtime>` | | extractors, engines |
| DuckDB | | the walking-skeleton demo + `--target ci` |
| `dbt-core` + `dbt-<adapter>` | | transform (prod-shaped) |
| `dbt-duckdb` | | transform tests, `--target ci` |
| `<task runner>` (make / just / task / nox) | | the targets below |
| `docker` + `docker-compose.yml` (optional) | | mock source services for integration checks |

Install: `<task> setup` (creates the venv / installs deps / pulls pre-commit).
The demo needs only DuckDB + the runtime — no dbt, no containers.

## Task targets

| Target | Does |
|--------|------|
| `<task> demo` / `demo-good` / `demo-fixed` / `demo-fail` | **runnable** walking-skeleton slice: load → DQ quarantine → reconciliation gate → publish/block. No cloud/dbt/orchestrator. See `build/repo/DEMO.md`. |
| `<task> setup` | install everything |
| `<task> lint` | formatter + `sqlfluff` + type-check |
| `<task> test` | all unit tests (incl. the real `test_demo.py`) + `dbt build --target ci` on fixtures |
| `<task> test-<component>` | one component's unit tests |
| `<task> dbt-ci` | `dbt build --target ci` only |
| `<task> golden-update` | regenerate `tests/golden/` (review the diff!) |
| `<task> run-<extractor> --date <d>` | run one extractor against a mock / sample |

## How each source is faked locally

| Source | Local stand-in |
|--------|----------------|
| SQL DB | containerised engine seeded from `fixtures/<src>/sample.sql`, or a DuckDB file |
| REST API | a local mock server (recorded responses) or `responses`/`vcr`-style fixtures |
| SFTP / object store | a local folder that mirrors the key layout |
| BigQuery / warehouse read | a Parquet/CSV fixture + a thin adapter seam |
| Target warehouse | DuckDB via `dbt --target ci` |

## The loop

0. Build the **walking skeleton** first (`build-plan.md` Component 0 /
   `demo-harness.md`): one source, extract/load → transform → one DQ quarantine →
   reconcile → published `gold` table, with real small bodies. `<task> demo` must
   run before any stub work.
1. Pick the next component from `build-plan.md`.
2. Create files per its buildsheet.
3. `<task> test-<component>` until green.
4. `<task> test` (full) stays green.
5. Tick the buildsheet's done checklist; commit.

Phase 4 lifts this repo into the real project repo and wires CI to `<task> test`.
