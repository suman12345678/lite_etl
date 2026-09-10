# Test strategy

> Phase 5 deliverable. The full test picture for this pipeline. Unit tests were
> written in Phase 3; this file adds integration, contract, end-to-end and data
> tests, and says what gates merge vs deploy.

- **Project:**  - **Date / version:**
- **Baseline:** `design/`, `build/`, `pipeline/`

## The pyramid

| Layer | Scope | Tooling | Runs in | Gates |
|-------|-------|---------|---------|-------|
| Unit (Phase 3) | one component / model, mocked deps | `<task> test`, `dbt build --target ci` (DuckDB) | PR | merge |
| Data tests | dbt generic + `dbt_expectations` + singular | `dbt build` / `dbt test` | PR + every run | merge + run |
| Integration | 2-3 real components together against a real dev warehouse + real storage | `<task> test-integration` | PR (nightly if slow) | merge or nightly |
| Contract | source schema + downstream `gold` schema stability | `dbt source` checks, schema snapshots, consumer contract tests | PR | merge |
| End-to-end | one golden business date through the whole pipeline in dev | orchestrator run + assertions on `gold` + recon report | nightly + pre-promote | promote |

## Coverage targets

- Extract / transform / reconciliation logic: **>= <n>%** line coverage.
- Every documented failure mode has a test (unit or integration).
- Every DQ rule in `04` has a row in `dq-behaviour-matrix.md`.
- Every reconciliation check in `05` has PASS + FAIL + boundary fixtures.

## Environments for testing

| Test layer | Warehouse | Storage | Sources |
|------------|-----------|---------|---------|
| unit / data | DuckDB | local files | fixtures |
| integration | dev warehouse | dev bucket | fixtures loaded to a test schema |
| e2e | dev warehouse (isolated schema) | dev bucket | recorded / synthetic full-day set |

## Test data

- Synthetic or masked only; never production rows in a repo or a shared env.
- The "golden business date" set: one realistic day per source, committed,
  regenerated deliberately.

## What is explicitly NOT tested here

_(e.g. the warehouse engine itself, third-party API correctness, the BI layer -
out of scope per `00`.)_
