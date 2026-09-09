# 04 - Data quality

## Dimensions to enforce

| Dimension | Enforce? | Notes |
|-----------|----------|-------|
| Completeness (required, not-null, fill-rate) | | |
| Validity (type, range, regex, allowed values) | | |
| Uniqueness (key uniqueness, dedupe) | | |
| Consistency (cross-field, cross-row, cross-dataset) | | |
| Referential integrity (FK exists in reference / prior load) | | |
| Timeliness (freshness window, no future dates) | | |
| Accuracy (check digits, tolerance vs source of truth) | | |

## Concrete rules

| Field / entity | Rule | Severity (info/warn/error) | On failure (fail run / quarantine / fix / warn) |
|----------------|------|----------------------------|-------------------------------------------------|
| | | | |

## Thresholds

- Fail the run if: _e.g. reject rate > 0.5%_
- Warn if: _e.g. reject rate > 0.1%_
- Per-partition or whole-run:

## Reporting & ownership

- **DQ report goes to:** (who / where / cadence)
- **DQ score tracked?** yes / no - definition:
- **Owner of source-data fixes:**
