# Component buildsheet: `lineage` (metadata / lineage emitter)

- **Design refs:** `design/component-design.md` (Lineage / metadata),
  `design/architecture-overview.md` §4, `requirements/06` (column-level lineage:
  run manifests + dbt manifest + UC lineage -> OpenLineage)
- **Language / framework:** Python 3.12; OpenLineage client (or a thin HTTP POST)
- **Repo path:** `build/repo/lineage/`

## Files to create

| Path | Purpose |
|------|---------|
| `build/repo/lineage/__init__.py` | |
| `build/repo/lineage/emit.py` | assemble + send lineage events for a run |
| `build/repo/lineage/dbt_manifest.py` | parse dbt `manifest.json` -> model + column edges |
| `build/repo/tests/unit/test_lineage.py` | |

## Public interface

- **`emit(run_id, business_date, manifests: list[Path], dbt_manifest: Path, settings)`**
  - Reads each extractor `manifest.json` (source -> `bronze` edge) and the dbt
    `manifest.json` (`bronze` -> `silver` -> `gold` model + column edges).
  - Builds OpenLineage `RunEvent`s (job = pipeline, run = `run_id`, inputs /
    outputs with column-lineage facets).
  - POSTs to `settings.lineage.endpoint` (no-op logs the payload when unset).
- **`trace(gold_table, key) -> LineagePath`** - dev/debug helper: given a `gold`
  row key, return source extract `run_id`(s), inbound files, dbt model git SHA,
  and the reconciliation report uri.

## Config keys

| Key | Type | Required | Notes |
|-----|------|----------|-------|
| `lineage.endpoint` | str | no | OpenLineage collector URL; unset -> log only |
| `lineage.namespace` | str | no | default `northwind_<env>` |
| `storage.manifests_uri` / `recon_uri` | str | yes | inputs |

## Key logic

1. Collect run manifests for the business date.
2. Parse the dbt manifest: nodes + `depends_on` + `columns` -> edges.
3. Merge into one graph keyed by `run_id`.
4. Emit events (start on ingest, complete on publish); attach a `dbt_model_sha`
   facet from the git SHA in the manifest.

## Unit tests to write

| Test | Fixture | Asserts |
|------|---------|---------|
| manifest parse | a small dbt `manifest.json` fixture | expected model + column edges |
| event assembly | 2 extractor manifests + dbt manifest | one RunEvent per job, inputs/outputs correct, column facet present |
| endpoint unset | no `lineage.endpoint` | logs the payload, returns without error |
| endpoint error | mock 500 | retried once then a warning, run not failed (lineage is best-effort) |
| trace helper | fixture graph | returns source `run_id`, files, model SHA, recon uri for a known key |

## Fixtures needed

`fixtures/lineage/dbt_manifest.json` (trimmed), two `manifest.json` samples.

## Done checklist

- [ ] files created  - [ ] parses dbt manifest columns
- [ ] best-effort (never fails the run)  - [ ] `trace` helper works
- [ ] wired into `make test`
