# Fixtures catalog

> Phase 3 deliverable. Every fixture the unit tests need, by source. Fixtures are
> small, committed, and contain **no real data or secrets**. Edge-case fixtures
> come straight from the "Known quirks" in `requirements/01-source-systems.md`
> and the DQ rules in `04-data-quality.md`.

- **Location:** `build/repo/tests/fixtures/`
- **Golden outputs:** `build/repo/tests/golden/` (expected results to diff against)
- **Real vs placeholder:** the walking-skeleton source's `sample`, `bad_rows`,
  `bad_rows_fixed` and the `recon/control_totals_*` files must have **real
  content** (the demo runs on them). Other sources may start as a one-line
  `README` placeholder and get real rows when that component is implemented -
  mark which is which in the "Represents" column.

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
| `golden/<entity>.csv` | dbt marts / the demo slice on the `sample` fixtures | at least one must be **real content** (the walking-skeleton entity); regenerate with `<task> golden` on an intentional logic change |

## Reconciliation fixtures (shared with Phase 5)

| Fixture | Scenario | Expected gate |
|---------|----------|---------------|
| `recon/control_totals_pass.csv` | control totals align with the clean data | PASS |
| `recon/control_totals_fail.csv` | control total outside tolerance | FAIL, publish blocked |
| `recon/control_totals_fixed.csv` | the corrected-data control total | PASS after the source fix |
| `recon/pass.*` / `fail_count.*` / `fail_total.*` / `boundary.*` | full 8-check set (Phase 5) | per `reconciliation-fixtures.md` |

## Rules

- No PII, no production rows. Synthesise or heavily mask.
- Keep each fixture < a few KB; one concern per fixture.
- A new failure mode in a buildsheet must add a fixture here.
