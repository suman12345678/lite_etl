# Component buildsheet: `publisher`

- **Design refs:** `design/component-design.md#publisher`,
  `design/pipeline-blueprint.md` (`publish` -> `catalog_register` ->
  `advance_watermarks`), `requirements/02` (idempotency), `requirements/06`
  (catalog register + lineage)
- **Language / framework:** Python 3.12; Databricks SQL / Delta; local backend =
  DuckDB
- **Repo path:** `build/repo/publish/`

## Files to create

| Path | Purpose |
|------|---------|
| `build/repo/publish/__init__.py` | |
| `build/repo/publish/publish.py` | commit the reconciled business date to `gold` / `gold_pii` |
| `build/repo/publish/catalog.py` | set UC table properties / comments / tags from `_models.yml`; emit `_SUCCESS` |
| `build/repo/tests/unit/test_publish.py` | |

## Public interface

- **`publish(business_date, run_id, target, recon: ReconResult, settings) -> PublishResult`**
  - **Precondition:** `recon.verdict == "PASS"` - else raise
    `ReconciliationNotPassed` and do nothing.
  - One transaction per table group (`core`, `sales`, `web`, `wholesale`, `pii`)
    per business date; on any failure nothing in that group commits.
  - Emits `_SUCCESS` marker + a lineage event (hands to `lineage`).
  - Calls `StateStore.commit_watermark(run_id)` **last** (watermark advances only
    after a successful publish).
  - Returns `PublishResult(groups_committed, delta_versions, success_marker_uri)`.
- **`rollback(business_date, target, to_version: dict[str,int], settings)`** -
  Delta `RESTORE ... TO VERSION AS OF` per table (used by the runbook).

## Config keys

| Key | Type | Required | Notes |
|-----|------|----------|-------|
| `catalog` | str | yes | `northwind_<env>` |
| `publish.table_groups` | list | no | default `[core, sales, web, wholesale, pii]` |
| `storage.recon_uri` | str | yes | where `_reconciliation.json` + `_SUCCESS` live |

## Key logic

1. Assert `recon.verdict == "PASS"`.
2. For each table group: begin -> upsert/merge the built `gold.*` for
   `business_date` -> set table comments/properties -> commit.
3. Write `_SUCCESS` to `<recon_uri>/dt=<D>/`.
4. `lineage.emit(run_id, ...)`.
5. `StateStore.commit_watermark(run_id)`.

## Unit tests to write

| Test | Fixture | Asserts |
|------|---------|---------|
| happy publish | `ReconResult(PASS)` + built `gold` fixture | all groups committed, `_SUCCESS` written, watermark committed |
| recon FAIL blocks | `ReconResult(FAIL)` | raises `ReconciliationNotPassed`, nothing committed, watermark NOT advanced |
| group txn atomic | monkeypatch `sales` commit to raise | `core` may commit, `sales` fully rolled back, no `_SUCCESS`, watermark NOT advanced |
| re-publish same date | publish `D` twice | second run is a no-op merge, identical result, watermark committed once |
| watermark ordering | any happy publish | `commit_watermark` called strictly after all group commits + `_SUCCESS` |
| rollback | publish then `rollback` to prior versions | tables at prior Delta version, marker cleared |

## Fixtures needed

A tiny built-`gold` fixture set (a few rows per table) + a `ReconResult` builder
in `conftest.py`.

## Done checklist

- [ ] files created  - [ ] recon-PASS precondition enforced
- [ ] per-group atomicity  - [ ] watermark advances only after `_SUCCESS`
- [ ] re-publish is idempotent  - [ ] wired into `make test`
