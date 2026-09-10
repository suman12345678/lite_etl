# Component buildsheet: `dbt` (transform + data quality)

- **Design refs:** `design/transformation-design.md` (whole file),
  `design/component-design.md#dbt-runner`, `design/data-entity-diagram.md`,
  `requirements/03` (business rules), `requirements/04` (DQ rules)
- **Framework:** dbt Core 1.8, `dbt-databricks` (runtime), `dbt-duckdb` (`ci`)
- **Repo path:** `build/repo/dbt/`
- **Companion doc:** [`dbt-project-scaffold.md`](dbt-project-scaffold.md) - the
  full tree + the model -> design-section map. This buildsheet covers the
  **runner wrapper** and the build/test contract.

## Files to create

| Path | Purpose |
|------|---------|
| `build/repo/dbt/` (full tree) | see `dbt-project-scaffold.md` |
| `build/repo/extractors/common/dbt_runner.py` | thin wrapper: assemble `dbt build` argv, inject `profiles.yml`, pass `--vars`, parse `run_results.json` |
| `build/repo/tests/unit/test_dbt_runner.py` | wrapper logic only (arg assembly, result parsing) |
| dbt tests run via `make dbt-ci` | not a Python unit test |

## Public interface (`dbt_runner.py`)

- **`run_build(select: str, target: str, business_date: date, run_id: str, *, defer_state: str | None = None, full_refresh: bool = False) -> DbtResult`**
  - Assembles `dbt build --select <select> --target <target> --vars '{business_date: ..., run_id: ...}'`
    (+ `--defer --state <defer_state>` for slim CI, + `--full-refresh` when
    allowed).
  - Runs it (subprocess), captures `run_results.json` + `manifest.json`.
  - Returns `DbtResult(ok, models_run, tests_passed, tests_failed, failed_nodes, manifest_path)`.
- **`run_tests(select: str, target: str) -> DbtResult`** - `dbt test --select <select>`
  (used by `reconciliation` for `tag:recon`).

## Selectors (from `transformation-design.md` s.10)

| Name | Selector |
|------|----------|
| `curated_build` | `staging+ intermediate+ marts+ --exclude tag:recon` |
| `reconcile` | `tag:recon` |
| slim CI | `state:modified+ --defer --state <prod manifest>` |

## DQ contract (from `requirements/04` + `dq-behaviour-matrix.md` in Phase 5)

- Generic tests (`not_null`, `unique`, `accepted_values`, `relationships`) on
  every key + enum, `severity: error`.
- `dbt_expectations` for ranges / regex / row counts / distribution.
- Singular tests in `dbt/tests/` for reject-rate threshold and PII-leak.
- A failing `error`-severity test aborts `dbt build` and its downstream -> no
  publish.
- Quarantined rows -> `silver.reject__<entity>` with `reason_code`, `_run_id`,
  `_dq_rule`.

## Unit tests to write (wrapper only)

| Test | Fixture | Asserts |
|------|---------|---------|
| argv assembly | select + target + date | exact `dbt build` argv, `--vars` JSON well-formed |
| slim-CI argv | `defer_state` set | `--defer --state <path>` appended |
| full-refresh guard | `target="prd"`, `full_refresh=True`, no release flag | raises `FullRefreshNotAllowed` |
| result parse - pass | a sample `run_results.json` (all pass) | `ok=True`, counts correct |
| result parse - fail | sample with 1 failed test | `ok=False`, `failed_nodes` names it |

## dbt `--target ci` gate (`make dbt-ci`)

- Seeds + fixtures (as `bronze` stand-ins) loaded into DuckDB.
- `dbt build --target ci` runs every model + generic/expectation test + snapshot.
- Must be green before Phase 4. Golden output diff via `make golden`.

## Fixtures needed

The seed CSVs (in the scaffold) + `tests/fixtures/*` promoted into DuckDB
`bronze.*` tables by `tests/conftest.py` / a `dbt/seeds/_ci/` set. See
`dbt-project-scaffold.md` §"Fixtures for --target ci".

## Done checklist

- [ ] full `dbt/` tree scaffolded (see scaffold doc)
- [ ] `dbt_runner.py` + its unit tests pass
- [ ] `make dbt-ci` runs `dbt parse` clean (stubs compile) - model bodies are `TODO`
- [ ] every `requirements/04` rule has a test entry in a `_models.yml` or `tests/`
- [ ] wired into `make test`
