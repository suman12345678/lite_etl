# dbt project scaffold

> Phase 3 deliverable. The concrete dbt project tree to create under
> `build/repo/dbt/`, and the map from each model / test / snapshot / seed to the
> Phase 2 design section it implements. For a non-dbt transform tool, keep the
> headings and describe the equivalent module layout.

- **Framework / adapter:** (from `10-platform-and-deployment.md`)
- **Design baseline:** `design/transformation-design.md`, `data-entity-diagram.md`

## Tree to create

```
build/repo/dbt/
  dbt_project.yml
  packages.yml
  profiles/profiles.yml           # targets: ci (duckdb), dev, ...
  models/
    staging/<src>/stg_<src>__<entity>.sql   + _<src>__sources.yml + _<src>__models.yml
    intermediate/<domain>/int_<domain>__<step>.sql
    marts/<domain>/dim_<x>.sql  fct_<y>.sql  + _<domain>__models.yml
  snapshots/<entity>_snapshot.sql
  seeds/<reference>.csv
  macros/<project macros>.sql
  tests/<singular tests>.sql
```

## Model map

| dbt object | File | Implements (design ref) | Materialisation | Tests attached |
|------------|------|-------------------------|-----------------|----------------|
| `stg_<src>__<entity>` | `models/staging/...` | transformation-design s.2; 03 | view | not_null/unique on key |
| `int_<domain>__<step>` | `models/intermediate/...` | transformation-design s.2; 03 rules | ephemeral | - |
| `dim_<x>` | `models/marts/...` | data-entity-diagram; 02 load pattern | table | unique key, relationships |
| `fct_<y>` | `models/marts/...` | data-entity-diagram (grain); 02 | incremental (`<strategy>`) | not_null FKs, `dbt_expectations` ranges |
| `<entity>_snapshot` | `snapshots/...` | transformation-design s.5; 03 historisation | snapshot | valid_to continuity |

Snapshot stubs must still be **valid**: `strategy='timestamp'` needs a real
`updated_at` column in the `select`; `strategy='check'` needs `check_cols=[...]`
or `'all'` and no `updated_at`. If the stub `select` cannot yet expose the
timestamp column, exclude `path:snapshots` from the `--target ci` build until the
body is real, and say so here.
| `<reference>.csv` | `seeds/...` | 03 reference data | seed | accepted_values |
| singular test `<name>` | `tests/...` | 05 recon check / 08 PII-leak | - | tag `recon` / `security` |

## Macros to create

| Macro | Purpose | Design ref |
|-------|---------|-----------|
| `surrogate_key()` | wrap the hash impl so it is swappable | transformation-design s.8 |
| `<engine shim>` | isolate engine-specific SQL (MERGE / QUALIFY / OPTIMIZE / ...) | portability stance |
| `<currency / naming / ...>` | | 03 |

## Run targets

- `dbt build --target ci` - full build + test on DuckDB with seeds + fixtures
  (Phase 3 gate).
- `dbt build --select <pipeline selector> --target dev` - per-pipeline (Phase 4).
- `dbt test --select tag:recon` - the reconciliation gate step.

## CI source shim - how fixtures become `bronze.*`

`dbt build --target ci` needs the `bronze.<src>__<obj>` relations its `source()`s
point at to *exist* in the DuckDB file. Scaffold **one** of these (state which):

- **Shared loader (preferred):** a `demo/load.py::load_fixtures_to_duckdb(db_path)`
  that reads `tests/fixtures/<src>/*` and `CREATE`s `bronze.<src>__<obj>` (with
  `_run_id` / `_source_file` / `_extracted_at` / `_ingest_date` columns).
  `tests/conftest.py` calls it before the dbt run; the walking-skeleton demo
  calls the same function. One loader, one bronze shape.
- **Seeds-as-sources:** put the fixture rows in `seeds/_ci/<src>__<obj>.csv` and
  override `generate_schema_name` so the `ci` target lands them in a `bronze`
  schema; `sources.yml` resolves to them only under `--target ci`.
- **`read_*` macro:** a `bronze()` macro that returns `read_parquet('fixtures/...')`
  when `target.name == 'ci'` and `source(...)` otherwise.

`tests/conftest.py` must be **real** (not `raise NotImplementedError`): a
`bronze_db` / `settings` fixture that produces a loaded DuckDB file.

## Fixtures for `--target ci`

_List the seed CSVs / fixture sources that stand in for `bronze` in local
tests; cross-reference `fixtures-catalog.md`. The walking-skeleton source's
fixtures must be real content (not placeholders)._
