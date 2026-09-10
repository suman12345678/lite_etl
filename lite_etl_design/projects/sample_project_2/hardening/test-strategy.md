# Test strategy - Northwind Commerce (DEMO)

> Phase 5 deliverable. The full test picture. Unit tests were written in Phase 3
> (`build/repo/tests/unit/`, 14 stubs); this file adds data, integration,
> contract and end-to-end tests, and says what gates merge vs deploy vs promote.

- **Project:** Northwind Commerce - Unified Retail Analytics Harness
- **Date / version:** 2026-09-09 / v1.0
- **Baseline:** `design/`, `build/` (`build-plan.md`, `fixtures-catalog.md`), `pipeline/`

## The pyramid

| Layer | Scope | Tooling | Runs in | Gates |
|-------|-------|---------|---------|-------|
| **Unit** (Phase 3) | one extractor / engine fn / dbt model, deps mocked (`respx`, DuckDB) | `pytest` (`make test-<slug>`), `dbt build --target ci` on DuckDB | PR | **merge** |
| **Data tests** | dbt generic + `dbt_expectations` + singular + `elementary` anomaly | `dbt build` / `dbt test` | PR (slim) + every scheduled run | **merge** + **run** |
| **Contract** | `sources.yml` schema stability; `gold.*` output schema; exposures resolve | schema-snapshot diff, `dbt ls --select exposure:*` | PR | **merge** (unless `contract-change` label) |
| **Integration** | 2-3 real components against the **dev** Databricks workspace + dev S3, isolated schema | `pytest -m integration` (`make test-integration`) | PR (fast subset) + nightly (full) | **merge** (subset) / **nightly** |
| **End-to-end** | one golden business date through the whole Dagster graph in dev | `dagster job execute` + assertions on `gold` + `_reconciliation.json` | nightly + pre-promote | **promote** |

## Coverage targets

- Extractor / landing / `recon` / `publish` logic: **>= 80%** line coverage
  (already the `pyproject.toml` `--cov` gate; enforce `--cov-fail-under=80` in CI - **TODO** add flag).
- Every documented failure mode in the 9 buildsheets + `component-design.md` has
  a test (unit or integration) - traceability column in `integration-e2e-plan.md`.
- Every DQ rule in `requirements/04` has >= 1 pass row and >= 1 fail/quarantine
  row in `dq-behaviour-matrix.md`.
- Every reconciliation check in `requirements/05` has PASS + FAIL + boundary
  fixtures in `reconciliation-fixtures.md`.
- Every paging alert in `observability-wiring.md` has a synthetic-failure test
  fired once in dev (go-live drill).

## Environments for testing

| Test layer | Warehouse | Storage | Sources | PII |
|------------|-----------|---------|---------|-----|
| unit / data / contract | DuckDB (`--target ci`) | local `tests/fixtures/` | committed fixtures | fake only (`@example.test`) |
| integration | dev workspace, schema `ci_int_<run>` (dropped after) | `s3://northwind-dev-inbound` test prefix | fixtures loaded to a test schema | hashed; `gold_pii` synthetic |
| e2e | dev workspace, catalog `northwind_dev`, schema `e2e_<date>` | dev buckets | the golden full-day synthetic set | hashed; `gold_pii` synthetic |

- **dev** normal data = masked **5%** sample of prod (`requirements/09`); **stg**
  = full masked copy refreshed weekly. E2E uses the committed synthetic golden
  day, not the sample, so it is deterministic.

## Test data

- **Synthetic or masked only.** Never production rows in a repo or a shared env.
  `gold_pii` is always synthetic outside prod. Fake emails `@example.test`.
- **The "golden business date" set:** one realistic day per source
  (`tests/fixtures/<src>/sample.*` + a `golden/` expected `dim_customer.csv` /
  `fct_order.csv`), committed, regenerated only on an intentional logic change
  via `make golden` (`tests/regen_golden.py`).
- **Reconciliation fixtures** live in `tests/fixtures/recon/` and are shared with
  `reconciliation-fixtures.md`.
- **Black Friday profile:** a 5x-volume variant of the golden day for the
  performance check (`E8`), generated, not committed at full size.

## What is explicitly NOT tested here

- Databricks / Delta / Spark engine correctness, `dagster` and `dbt` internals.
- Third-party API correctness (Shopify, Salesforce, GA4, `open.er-api.com`) -
  contract tests cover *our* handling of their schema, not their behaviour.
- The Looker semantic model and the Braze reverse-ETL job - client-owned,
  out of scope per `00`; contract test `C3` only checks the `gold` exposures
  still resolve.
- Load/scale beyond the Black-Friday 5x profile; true DR region failover is a
  **drill** (`go-live-checklist.md`), not an automated test.
