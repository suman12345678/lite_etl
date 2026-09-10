# Local development - Northwind Commerce (DEMO)

> Phase 3 deliverable. How to run every component on a laptop with no cloud
> access - the loop developers and CI both use.

- **Repo:** `build/repo/`

## Prerequisites

| Tool | Version | For |
|------|---------|-----|
| Python | 3.12 | extractors, recon, publish, lineage, obs |
| `uv` | latest | dependency + venv management |
| `make` | any | the targets below |
| `dbt-core` + `dbt-databricks` + `dbt-duckdb` | 1.8.x | transform (prod-shaped + local) |
| Docker | optional | Postgres stand-in for `oltp` integration checks |

Install: `make setup` (creates `.venv` via `uv`, installs
`pyproject.toml` deps + dbt packages, installs pre-commit).

## Make targets

| Target | Does |
|--------|------|
| `make demo` / `demo-good` / `demo-fixed` / `demo-fail` | **runnable** DuckDB walking-skeleton: load → DQ quarantine → reconciliation gate → publish. No cloud/dbt/Dagster. See `build/repo/DEMO.md`. |
| `make setup` | install everything |
| `make lint` | `ruff` + `sqlfluff` + `mypy` |
| `make test` | all unit tests + `dbt build --target ci` on fixtures |
| `make test-<slug>` | one component's unit tests (`oltp`, `shopify`, `pos`, `salesforce`, `ga4`, `fx`, `config`, `secrets`, `landing`, `dbt-runner`, `reconcile`, `publish`, `lineage`, `observability`) |
| `make dbt-ci` | `dbt deps` + load fixtures into DuckDB + `dbt build --target ci` |
| `make golden` | regenerate `tests/golden/` (review the diff!) |
| `make run-<src> DATE=2026-09-08` | run one extractor against its local stand-in |
| `make clean` | drop `.venv`, `.local_state/`, `dbt/target/`, the DuckDB file |

## How each source is faked locally

| Source | Local stand-in |
|--------|----------------|
| `oltp` (Postgres) | `tests/fixtures/oltp/sample.sql` loaded into a DuckDB file (or `docker compose up pg` for integration) |
| `shopify` / `fx` (REST) | `respx`/`httpx` mock transport replaying `tests/fixtures/<src>/*.json` |
| `pos` (S3) | a local folder `tests/fixtures/pos/` mirroring `pos/dt=.../store=.../` |
| `salesforce` (Bulk API) | recorded CSV job results in `tests/fixtures/salesforce/` |
| `ga4` (BigQuery) | `tests/fixtures/ga4/sample.parquet` (the aggregation SQL is not run locally) |
| Databricks warehouse | DuckDB via `dbt --target ci` |
| Delta `bronze`/state | a parquet directory + `_delta_log` shim under `.local_state/` |
| secret scopes | env vars `NW_SECRET__<SYSTEM>__<FIELD>` (see `.env.example`) |

## The loop

1. Pick the next component from `build-plan.md` §1.
2. Create files per its buildsheet.
3. `make test-<slug>` until green.
4. `make test` (full) stays green.
5. Tick the buildsheet's done checklist; commit.

Phase 4 (`/assemble-pipeline`) lifts this repo into the real `northwind-data`
repo, adds `infra/` + `dagster/` + `.github/workflows/`, and wires CI to
`make lint && make test`.
