# Local development

> Phase 3 deliverable. How to run every component on a laptop with no cloud
> access - the loop developers and CI both use.

- **Repo:** `build/repo/`

## Prerequisites

| Tool | Version | For |
|------|---------|-----|
| `<language runtime>` | | extractors, engines |
| `dbt-core` + `dbt-<adapter>` | | transform (prod-shaped) |
| `dbt-duckdb` | | transform tests, `--target ci` |
| `<task runner>` (make / just / task / nox) | | the targets below |
| `<container runtime>` (optional) | | mock source services |

Install: `<task> setup` (creates the venv / installs deps / pulls pre-commit).

## Task targets

| Target | Does |
|--------|------|
| `<task> setup` | install everything |
| `<task> lint` | formatter + `sqlfluff` + type-check |
| `<task> test` | all unit tests + `dbt build --target ci` on fixtures |
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

1. Pick the next component from `build-plan.md`.
2. Create files per its buildsheet.
3. `<task> test-<component>` until green.
4. `<task> test` (full) stays green.
5. Tick the buildsheet's done checklist; commit.

Phase 4 lifts this repo into the real project repo and wires CI to `<task> test`.
