# Component buildsheet: `landing` (landing writer)

- **Design refs:** `design/architecture-overview.md` §2 `Landing writer`,
  `design/component-design.md#extractor` (land raw + manifest),
  `design/data-flow-diagram.md` Shape B (POS supersede), `requirements/02`
- **Language / framework:** Python 3.12; Delta via `deltalake`; local backend =
  DuckDB / parquet directory
- **Repo path:** `build/repo/extractors/common/landing.py`

## Files to create

| Path | Purpose |
|------|---------|
| `build/repo/extractors/common/landing.py` | `write_bronze()` + `write_manifest()` + POS supersede |
| `build/repo/extractors/common/manifest.py` | `Manifest` dataclass + (de)serialise |
| `build/repo/tests/unit/test_landing.py` | |

## Public interface

- **`write_bronze(result: ExtractResult, *, source, object, business_date, run_id, settings) -> LandResult`**
  - Appends the extractor's Parquet to `bronze.<source>__<object>` (Delta),
    tagging every row `_run_id`, `_source_file`, `_extracted_at`, `_ingest_date`
    (+ `_file_etag`, `_superseded` for `pos`).
  - Atomic: writes to a temp path then a single Delta commit; on failure nothing
    is visible.
  - Returns `LandResult(landed_rows, table, delta_version)`.
- **`supersede_prior(source="pos", *, business_date, store, new_etag, settings)`**
  - Sets `_superseded = true` on rows for `(business_date, store)` whose
    `_file_etag != new_etag`. Rows are kept, never deleted.
- **`write_manifest(manifest: Manifest, settings)`** - writes `manifest.json`
  (source, object, window, `run_id`, row counts, checksums, `_source_file` list)
  to `<manifests_uri>/<source>/<object>/dt=<D>/run_id=<run_id>/manifest.json`.

## Config keys

| Key | Type | Required | Notes |
|-----|------|----------|-------|
| `storage.landing_uri` | str | yes | `bronze` root |
| `storage.manifests_uri` | str | yes | manifest root |
| `landing.local_backend` | bool | no | true when `catalog == "duckdb"` |

## Key logic

1. Validate the Parquet schema against the extractor's declared columns.
2. Add the `_` audit columns.
3. Temp-write -> Delta `append` in one commit (`deltalake.write_deltalake` with
   `mode="append"`). Local: append to a parquet dir + a `_delta_log` shim.
4. For `pos`: after the append, call `supersede_prior`.
5. Write the manifest last (so a manifest always implies a committed append).

## Unit tests to write

| Test | Fixture | Asserts |
|------|---------|---------|
| happy path | a small `ExtractResult` | rows in `bronze.<src>__<obj>`, all `_` columns set, manifest file exists |
| atomic on failure | monkeypatch the commit to raise mid-write | no rows visible, no manifest |
| idempotent (new run_id) | land same data twice, different `run_id` | both sets present, distinct `_run_id`; no dedupe here |
| POS supersede | land etag A, then etag B for same `(D, store)` | A rows `_superseded=true`, B rows `_superseded=false`, nothing deleted |
| schema mismatch | Parquet missing a declared column | raises `LandingSchemaError` before any write |
| manifest contents | any land | manifest has row count == landed rows, checksum matches, `_source_file` list present |

## Fixtures needed

Reuses the extractor `sample` outputs; a two-etag POS pair (see
`fixtures-catalog.md`).

## Done checklist

- [ ] files created  - [ ] interface matches  - [ ] atomicity + supersede tested
- [ ] `_run_id` never null  - [ ] manifest always written after a successful commit
- [ ] wired into `make test`
