# Component buildsheet: `config` (config loader + state store)

- **Design refs:** `design/component-design.md#state-store`,
  `design/deployment-and-iac.md` s.8 (config layering), `requirements/10` (config
  layering), `requirements/02` (idempotency - watermark model)
- **Language / framework:** Python 3.12, `pydantic` for typed config, Delta via
  `deltalake` / a thin seam for tests
- **Repo path:** `build/repo/extractors/common/`

## Files to create

| Path | Purpose |
|------|---------|
| `build/repo/extractors/common/config.py` | load + merge `config/defaults.yml` -> `config/<env>.yml` -> `config/<env>.generated.yml` -> env vars; return a typed `Settings` object |
| `build/repo/extractors/common/state.py` | read / write source watermarks and run registry in `_state.watermarks` (Delta); local backend = a DuckDB/parquet file |
| `build/repo/config/defaults.yml` | safe-everywhere defaults (lookbacks, page sizes, thresholds) |
| `build/repo/config/{dev,stg,prd}.yml` | per-env overlay skeletons (catalog, buckets, schedules, sizes) |
| `build/repo/tests/unit/test_config.py` | |
| `build/repo/tests/unit/test_state.py` | |

## Public interface

- **`load_settings(env: str, generated_path: str | None = None) -> Settings`**
  - Inputs: `env` in `{dev,stg,prd,ci}`; optional path to Terraform-written
    `<env>.generated.yml`; env vars override everything.
  - Output: frozen `Settings` (catalog, `landing_uri`, `inbound_uri`,
    `manifests_uri`, `recon_uri`, per-source `objects`/`lookback`/`page_size`,
    `dq.fail_threshold_pct`, `recon.tolerance_pct`, secret-scope prefix).
- **`StateStore(settings).get_watermark(source, object) -> Watermark | None`**
- **`StateStore.stage_watermark(source, object, value, run_id)`** - stages a new
  high-watermark; not durable until `commit_watermark(run_id)` (called by the
  publisher after reconcile PASS).
- **`StateStore.register_run(run_id, source, business_date, status)`**

## Config keys

| Key | Type | Default | Required | Notes |
|-----|------|---------|----------|-------|
| `catalog` | str | - | yes | `northwind_<env>` |
| `storage.landing_uri` | str | - | yes | `s3://…-lakehouse/bronze` |
| `storage.inbound_uri` | str | - | yes | `s3://…-inbound` |
| `sources.<src>.lookback_minutes` | int | 60 | no | incremental re-read window |
| `sources.<src>.page_size` | int | 1000 | no | |
| `dq.fail_threshold_pct` | float | 0.5 | no | from `04` |
| `recon.tolerance_pct` | float | 0.5 | no | from `05` |
| `secrets.scope_prefix` | str | `northwind/<env>` | yes | |

## Key logic

1. `load_settings`: read YAML layers in order, deep-merge, apply `NW_*` env-var
   overrides, validate with pydantic, freeze.
2. `StateStore`: watermark table schema `(source, object, watermark_value,
   watermark_type, run_id, staged_at, committed_at)`; `get` returns the latest
   **committed** row; `stage` upserts a row with `committed_at = NULL`; `commit`
   sets `committed_at = now()` for that `run_id`.
3. Local backend switch on `settings.catalog == "duckdb"` -> parquet file at
   `.local_state/`.

## Unit tests to write

| Test | Fixture | Asserts |
|------|---------|---------|
| happy path | `config/defaults.yml` + `config/dev.yml` | merged `Settings` has expected values |
| env-var override | monkeypatch `NW_DQ__FAIL_THRESHOLD_PCT=1.0` | override wins |
| missing required key | truncated `dev.yml` | raises `ConfigError` naming the key |
| watermark round-trip | fresh local state | `stage` then `commit` then `get` returns the value |
| staged not visible | `stage` without `commit` | `get` still returns the prior committed value |
| re-run same run_id | `stage` twice, `commit` once | one committed row, no duplication |

## Fixtures needed

`config/defaults.yml`, `config/dev.yml` (in the scaffold); a tmp state dir per
test (pytest `tmp_path`).

## Done checklist

- [ ] files created  - [ ] interface matches  - [ ] all tests pass
- [ ] runs locally (no cloud)  - [ ] config-driven  - [ ] wired into `make test`
