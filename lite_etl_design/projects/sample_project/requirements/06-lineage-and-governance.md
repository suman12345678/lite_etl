# 06 - Data lineage & governance

> DEMO - fictional. BCBS 239 makes lineage a first-class requirement here.

## Lineage

- **Granularity required:** **column-level** for every field that feeds a
  regulatory or GL figure; table-level minimum for everything else.
- **Capture mechanism:**
  - `manifest.json` per run (source object, query/file, row counts, checksums,
    `run_id`, code version, rule set version) - immutable in S3 and mirrored to
    a `CURATED.RUN_MANIFEST` table
  - OpenLineage events emitted by the ETL job and by dbt (`dbt-ol`) -> **DataHub**
  - every curated row carries `_source_run_id`, `_loaded_at`, `_dbt_invocation_id`
- **What must be traceable (success criterion):** for any published number, show
  source system + extract `run_id` + transformation version within 2 minutes.

## Catalog / metadata

- **Tool:** DataHub (managed)
- **Registered:** all `RAW`/`STAGING`/`CURATED` datasets, schemas, owners, tags
  (`pii`, `regulated`, `gl`), column descriptions, freshness, the OpenLineage graph
- **Business glossary:** regulatory terms (LCR, NSFR, RWA inputs), "business
  date", "reporting currency", "account status" - authored by Regulatory
  Reporting, linked to columns

## Ownership

| Dataset / domain | Owner | On-call | Consumers |
|------------------|-------|---------|-----------|
| `CURATED.*` (model) | Risk Data team | Risk Data on-call | Regulatory Reporting, Finance |
| `CURATED_SENSITIVE.*` | Risk Data + DPO | Risk Data on-call | named analysts only |
| `RAW/STAGING.general_ledger` | Finance Systems | Finance Systems | Risk Data |
| `RAW/STAGING.card_transactions` | Risk Data (feed), Cards (source) | Risk Data on-call | Risk Data |
| Reference data in repo | Risk Data | - | all |

## Audit & retention of metadata

- **Retain:** run manifests, schema history, reconciliation results, DQ reports,
  Airflow logs, dbt run artifacts
- **Retention period:** **7 years** (SOX + regulatory), aligned with curated data
- **Who can query the audit trail:** Risk Data, Internal Audit, external
  auditors (read-only role)

## Change management

- Schema changes to `CURATED` follow a data-contract PR: proposed change,
  impact on consumers, migration plan; requires Risk Data + at least one
  consumer approval.
- Breaking changes: **20 business days** notice to consumers; additive changes
  any time.
- Source schema drift is detected automatically (see design) and raises a ticket
  before it can change curated output.
