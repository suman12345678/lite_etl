# Data-quality rules for this source

> Reference: `docs/business-rules-catalog.md`. One row per check.

| Dimension | Field(s) | Rule | Params | Severity | On fail |
|-----------|----------|------|--------|----------|---------|
| completeness | customer_id | not_null | | error | reject row |
| completeness | * | min_fill_rate | 0.95 | warn | log |
| uniqueness | customer_id | unique | | error | reject dupes |
| validity | email | regex | RFC-lite email | warn | quarantine |
| validity | country_code | enum | ref: country_codes | error | reject row |
| validity | balance_amount | range | -1e9 .. 1e12 | error | reject row |
| timeliness | source_updated_at | not_future | skew: 5m | error | reject row |
| conformity | customer_name | trim; collapse_ws | | info | fix in place |
| pii | email | mask | policy: default | error | fix in place |
| standardization | country_code | upper | | info | fix in place |

Severity: info | warn | error.  On fail: fix in place | log | quarantine | reject row | fail run.
