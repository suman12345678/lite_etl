# Reconciliation fixtures

> Phase 5 deliverable. Per reconciliation check from `requirements/05` and
> `design/transformation-design.md` s.7: the fixtures that force a PASS, a FAIL,
> and the tolerance boundary, plus the gate behaviour each must produce.

- **Checks source:** `requirements/05-reconciliation.md`
- **Gate:** a FAIL blocks publish, exits non-zero, no `_SUCCESS`, watermark
  unchanged, alert fires (from `pipeline-blueprint.md`).
- **Fixture location:** `<repo>/tests/fixtures/recon/`

## Per check

### `<check name>` (e.g. row counts source vs target)

| Fixture | Setup | Expected verdict | Expected gate action |
|---------|-------|------------------|----------------------|
| `<check>_pass` | source count == landed + rejected + filtered | PASS | publish proceeds |
| `<check>_fail` | landed short by N rows | FAIL | publish blocked, alert, `_reconciliation.json` names the check |
| `<check>_boundary` | delta exactly at tolerance | documented (PASS or FAIL - state which) | matches verdict |

### `<check name>` (e.g. control totals / financial balancing)

| Fixture | Setup | Expected verdict | Gate |
|---------|-------|------------------|------|
| `_pass` | SUM(measure) within +-`<x>%` of control | PASS | publish |
| `_fail_high` | SUM over tolerance | FAIL | block |
| `_fail_low` | SUM under tolerance | FAIL | block |
| `_boundary` | exactly +-`<x>%` | documented | - |

(Repeat for every check in `05`: row counts, control totals, financial
balancing, column/set hash, referential coverage, duplicate check, distribution
drift.)

## Report assertions

For every fixture, assert `_reconciliation.json` contains, per check:
`expected`, `actual`, `delta`, `tolerance`, `verdict`, and (on FAIL) enough to
locate the break (partition / channel / key range).

## Replay assertion

Running the same business date twice with a `_pass` fixture: identical
`gold` output, reconciliation PASS both times, watermark advances once.
