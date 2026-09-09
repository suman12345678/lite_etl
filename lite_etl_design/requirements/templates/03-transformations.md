# 03 - Transformations

- **ETL or ELT:** transforms run in an engine before load / in SQL inside the
  target after load / mixed (describe the split)
- **Transformation tooling (if known):** dbt / Spark / pandas / SQL / other
  _(the tool, its layers, materialisations, tests and packages are detailed in
  `10-platform-and-deployment.md`; this file holds the business rules)_

## Per-source / per-entity transformation rules

### Entity: `<target entity or table>`

- **Source(s):**
- **Cleansing:** trim, case, whitespace collapse, encoding, type casts
- **Standardisation:** code/lookup mappings, units, currency, address/name norm
- **Deduplication:** duplicate key = ; winning record = (latest by ? / priority ?)
- **Joins / enrichment:** reference datasets, lookups, derived attributes
- **Business rules / derived measures:** _describe logic or link a spec_
- **Historisation:** SCD2? effective-dating? soft delete? which columns
- **Aggregations / rollups / snapshots:**
- **Rejected rows:** drop / quarantine / fix-in-place

## Reference data needed

| Reference set | Source | Refresh | Used by |
|---------------|--------|---------|---------|
| | | | |

## Surrogate key strategy

- Hash of business key / sequence / natural key only / none
