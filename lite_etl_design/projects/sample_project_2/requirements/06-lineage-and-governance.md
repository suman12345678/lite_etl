# 06 - Data lineage & governance

> DEMO - fictional.

## Lineage

- **Granularity required:** column-level for `silver` and `gold`; dataset-level
  for `bronze` inbound files.
- **Capture mechanism:** three layers combined -
  1. per-run **manifest.json** from each extractor (source query/window,
     `run_id`, row counts, `_source_file`, checksums) in `bronze`;
  2. **dbt** `manifest.json` + `catalog.json` + `run_results.json` per build
     (model-to-model + column lineage via `dbt-databricks` + sqlparse);
  3. **Unity Catalog lineage** (automatic table + column lineage for anything
     that runs through Databricks SQL / notebooks).
- **What must be traceable:** for any `gold` row - which source extract
  (`run_id`, window), which inbound files, which dbt model version (git SHA +
  `invocation_id`), and which reconciliation report signed it off.

## Catalog / metadata

- **Tool:** **Unity Catalog** as the operational catalog; dbt docs site for the
  model/column dictionary; UC lineage feeds an OpenLineage endpoint for a future
  DataHub rollout (not in this scope).
- **What gets registered:** catalogs, schemas, tables, columns, owners, tags
  (`pii`, `finance`, `marketing`), `gold` table descriptions and column comments
  sourced from dbt `_models.yml`.
- **Business glossary:** dbt `docs` blocks per metric (`gmv`, `aov`, `margin`,
  `active_customer`) rendered into the dbt docs site and set as UC column
  comments.

## Ownership

| Dataset / domain | Owner | On-call | Consumers |
|------------------|-------|---------|-----------|
| `bronze.*` | Data Platform | Platform on-call | Analytics Eng |
| `silver.*`, `gold.*` | Analytics Engineering | AE on-call (PagerDuty) | Finance, Marketing, Merchandising |
| `gold_pii.*` | Analytics Eng + DPO | AE on-call | `northwind_pii_readers` group only |
| dbt project / Terraform | Data Platform + AE | shared | - |

## Audit & retention of metadata

- **Retain:** run manifests, dbt `run_results`/`manifest`, reconciliation
  reports, Dagster run history, Terraform plan/apply logs, CI run logs.
- **Retention period:** 5 years for reconciliation reports and dbt manifests
  (Finance audit); 13 months for run logs.
- **Who can query the audit trail:** Analytics Eng, Platform, Internal Audit
  (read-only Databricks + S3 `_recon` prefix).

## Change management

- Source schema changes: the schema-drift check (area 01/04) fails the run and
  opens a ticket; a source contract (`bronze` expected schema in
  `sources.yml` + a JSON schema per inbound file) must be updated via PR.
- `gold` breaking changes: 10-business-day notice to consumers; deprecations via
  a dbt `exposure` + a `_deprecated` column window before removal.
- All model + infra changes go through PR review (area 10).
