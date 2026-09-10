# Component buildsheet: `reconciliation` (engine + gate)

- **Design refs:** `design/component-design.md#reconciliation-engine`,
  `design/transformation-design.md` s.7, `design/pipeline-blueprint.md` (the
  blocking `reconcile` asset check), `requirements/05`
- **Language / framework:** Python 3.12 (orchestration + manifest compare) +
  singular dbt tests (`tag:recon`)
- **Repo path:** `build/repo/recon/`

## Files to create

| Path | Purpose |
|------|---------|
| `build/repo/recon/__init__.py` | |
| `build/repo/recon/compare.py` | manifest-vs-bronze-vs-silver row-count identity per source/date |
| `build/repo/recon/report.py` | build `_reconciliation.json` (per check: expected, actual, delta, tolerance, verdict) |
| `build/repo/recon/gate.py` | run `tag:recon` dbt tests + `compare` -> overall PASS/FAIL; exit non-zero on FAIL |
| `build/repo/dbt/tests/recon_row_counts.sql` | singular test (in the dbt scaffold) |
| `build/repo/dbt/tests/recon_gmv_control_total.sql` | singular test |
| `build/repo/dbt/tests/recon_refund_balancing.sql` | singular test |
| `build/repo/tests/unit/test_reconcile.py` | |

## Public interface

- **`run_gate(business_date: date, run_id: str, target: str, settings) -> ReconResult`**
  1. `dbt_runner.run_tests("tag:recon", target)`.
  2. `compare.row_count_identity(business_date, settings)` for each source.
  3. `report.build(...)` -> write `_reconciliation.json` to `<recon_uri>/dt=<D>/`.
  4. `ReconResult(verdict: "PASS"|"FAIL", checks: list[CheckResult], report_uri)`;
     the caller (publisher / orchestrator) treats `FAIL` as a hard stop.
- **`CheckResult`**: `name, applies_to, expected, actual, delta, tolerance,
  verdict, detail` (detail locates the break: channel / partition / key range).

## Checks (from `requirements/05`)

| Check | Where | Tolerance | On FAIL |
|-------|-------|-----------|---------|
| row-count identity (source manifest == bronze == silver in + rejected + superseded) | `compare.py` | exact | block publish |
| per-channel GMV vs control total | dbt `recon_gmv_control_total.sql` | ±0.5% | block publish |
| refund balancing + linkage | dbt `recon_refund_balancing.sql` | exact linkage; amount ±0.01 | block publish |
| order == sum(lines) | dbt (also a generic-ish singular) | ±0.01 | block publish |
| FX coverage | dbt singular | exact (carry-forward first) | block publish |
| duplicate keys | dbt `unique` + singular | exact | block publish |
| distribution drift vs 28-day baseline | dbt `dbt_expectations` | ±30% warn / ±60% FAIL | warn / block |
| PII-leak | dbt `assert_no_pii_in_gold.sql` | exact | block publish |

## Unit tests to write

| Test | Fixture | Asserts |
|------|---------|---------|
| row-count identity PASS | `fixtures/recon/pass.*` | verdict PASS, all checks green |
| count mismatch FAIL | `fixtures/recon/fail_count.*` | verdict FAIL, the row-count check named, non-zero exit |
| GMV over tolerance FAIL | `fixtures/recon/fail_total.*` | verdict FAIL, `detail` names the channel |
| GMV at boundary | `fixtures/recon/boundary.*` | documented behaviour (PASS at exactly ±0.5%) |
| report shape | any run | `_reconciliation.json` has every check with expected/actual/delta/tolerance/verdict |
| idempotent | run gate twice on `pass` | identical verdict + report (bar timestamp), no side effects on `gold` |
| control file missing | remove `totals.csv` fixture | verdict FAIL, "control total file missing", source owner in `detail` |

## Fixtures needed

`fixtures/recon/{pass,fail_count,fail_total,boundary}.*` and the source
`totals`/`payout` control-total fixtures. Shared with Phase 5
`reconciliation-fixtures.md`.

## Done checklist

- [ ] `recon/` modules + the 3 singular dbt tests created
- [ ] every `requirements/05` check has PASS + FAIL coverage
- [ ] `gate.py` exits non-zero on FAIL and writes the report either way
- [ ] no auto-retry of reconciliation itself
- [ ] wired into `make test`
