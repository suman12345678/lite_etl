# 06 - Data lineage & governance

## Lineage

- **Granularity required:** dataset / table / column
- **Capture mechanism:** manifest per run / OpenLineage events / catalog
  integration / manual
- **What must be traceable:** _e.g. "for any curated row, which source extract,
  run id, and transformation version produced it"_

## Catalog / metadata

- **Tool:** DataHub / Collibra / Purview / Unity Catalog / Glue / file catalog / none
- **What gets registered:** datasets, partitions, schemas, owners, tags
- **Business glossary / semantic definitions to attach:**

## Ownership

| Dataset / domain | Owner | On-call | Consumers |
|------------------|-------|---------|-----------|
| | | | |

## Audit & retention of metadata

- **Retain:** run manifests / schema history / reconciliation results / run logs
- **Retention period:**
- **Who can query the audit trail:**

## Change management

- How schema changes are proposed, approved, and communicated
- Contract with consumers (notice period for breaking changes)
