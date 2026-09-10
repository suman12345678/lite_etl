# Fixtures catalog

> Phase 3 deliverable. Every fixture the unit tests need, by source. Fixtures are
> small, committed, and contain **no real data or secrets**. Edge-case fixtures
> come straight from the "Known quirks" in `requirements/01-source-systems.md`
> and the DQ rules in `04-data-quality.md`.

- **Location:** `build/repo/tests/fixtures/`
- **Golden outputs:** `build/repo/tests/golden/` (expected results to diff against)

## Per source

### `<source slug>`

| Fixture file | Represents | Used by |
|--------------|-----------|---------|
| `<src>/sample.<ext>` | a normal small extract (~20 rows) | extractor happy path, dbt `--target ci` seed |
| `<src>/empty.<ext>` | valid but zero rows | extractor + downstream empty handling |
| `<src>/late_data.<ext>` | rows with timestamps before the watermark | incremental lookback test |
| `<src>/duplicates.<ext>` | repeated business keys | dedupe / supersede test |
| `<src>/schema_drift.<ext>` | added / removed / retyped column | drift-check test |
| `<src>/bad_rows.<ext>` | nulls in required fields, out-of-range, bad encoding | DQ routing test (pass / warn / quarantine / fail) |
| `<src>/partial.<ext>` | truncated / split file | partial-delivery test (file sources) |

### Golden outputs

| Golden file | For | Notes |
|-------------|-----|-------|
| `golden/<entity>.csv` | dbt marts on the `sample` fixtures | regenerate with `<task> golden-update` when logic changes intentionally |

## Reconciliation fixtures (shared with Phase 5)

| Fixture | Scenario | Expected gate |
|---------|----------|---------------|
| `recon/pass.*` | counts + control totals align | PASS |
| `recon/fail_count.*` | landed != source count | FAIL, no publish |
| `recon/fail_total.*` | control total outside tolerance | FAIL |
| `recon/boundary.*` | delta exactly at tolerance | documented behaviour |

## Rules

- No PII, no production rows. Synthesise or heavily mask.
- Keep each fixture < a few KB; one concern per fixture.
- A new failure mode in a buildsheet must add a fixture here.
