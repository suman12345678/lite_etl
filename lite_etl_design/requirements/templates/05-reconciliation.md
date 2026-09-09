# 05 - Reconciliation

> Proving a load is correct before it is published / consumed.

## Checks

| Check | Applies to | Tolerance | On failure |
|-------|-----------|-----------|------------|
| Row counts (source == landed + rejected + filtered) | | exact / +-X% | block publish / alert / retry |
| Control totals (SUM/AVG/MIN/MAX of measures) | | | |
| Financial balancing (debits==credits, opening+delta==closing) | | | |
| Column / set hash (source fingerprint == target) | | | |
| Referential coverage (target keys covered by reference) | | | |
| Duplicate check (no unexpected dupes landed) | | | |
| Distribution drift (volume / null-rate / stats vs baseline) | | | |

## Gate behaviour

- A hard failure: blocks `_SUCCESS` / publish? yes / no
- CLI / pipeline exits non-zero on failure? yes / no
- Auto-retry before failing? attempts / backoff

## Authoritative control report

- Is there an external control total / report to reconcile against?
- Source, format, cadence, how it is fetched

## Granularity

- Per partition / per load / whole dataset
