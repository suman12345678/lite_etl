# Requirement -> design traceability - Meridian Trust (DEMO)

> Produced by `/design-architecture` on 2026-09-03. Every requirement file
> appears. Status: covered / partial / deferred.

| Req file | Item | Design element(s) | Status | Notes |
|----------|------|-------------------|--------|-------|
| 00-project-brief | close 9d→4d, zero re-filed submissions | hard reconciliation gate (ADR-003), lineage (06 design), idempotent re-runs (ADR-002) | covered | outcome measured post go-live |
| 00-project-brief | trace any number in 2 min | manifests → `RUN_MANIFEST`, OpenLineage → DataHub, `_source_run_id` on every row | covered | |
| 00-project-brief | budget < EUR 8k/month | warehouse auto-suspend + right-sizing, S3 lifecycle, smallest MWAA (arch-overview §4, pipeline policies) | partial | validated by monthly cost review after go-live |
| 01-source-systems | Oracle incremental on `LAST_MOD_TS` | source extractor + watermark in `PIPELINE_STATE`; data-flow "incremental" diagram | covered | |
| 01-source-systems | card SFTP file, 1-2 parts, TOTAL trailer, EBCDIC-ish | card file parser component; data-flow "file-arrival" diagram | covered | |
| 01-source-systems | GL from BigQuery snapshot | GL extractor; data-flow "daily snapshot" diagram | covered | |
| 01-source-systems | FX REST with holiday gaps | FX extractor + carry-forward logic; data-flow "reference" diagram | covered | |
| 01-source-systems | CRM incremental, PII-heavy | extractor + PII tokeniser; restricted load path | covered | |
| 02-targets-and-loading | RAW→STAGING→CURATED(+SENSITIVE) | zone model (arch-overview §1), zone contract (data-flow) | covered | |
| 02-targets-and-loading | SCD2 dims, snapshot/append facts | ER diagram (SCD2 cols), dbt transform component | covered | |
| 02-targets-and-loading | idempotent per business_date, no double count | ADR-002, publisher component | covered | |
| 02-targets-and-loading | 13-month backfill at go-live | pipeline blueprint "Backfill" policy | covered | weekend run on `L` warehouse |
| 03-transformations | ETL/ELT split | ADR-001, component-design (parser, tokeniser, dbt) | covered | |
| 03-transformations | FX conversion to EUR | `DIM_FX_RATE` + fact `amount_eur`/`balance_eur` (ER, data-flow) | covered | |
| 03-transformations | dedupe card `(txn_id, post_date)` | STAGING dedupe task (pipeline blueprint), DQ uniqueness | covered | |
| 04-data-quality | 7 dimensions, thresholds | DQ engine component; STAGING DQ checkpoint; dbt tests | covered | rule set versioned in config |
| 04-data-quality | GL debits==credits zero tolerance | DQ rule + reconciliation "financial balance" check | covered | blocks publish |
| 04-data-quality | quarantine not drop | `*_QUARANTINE` tables + reason codes (data-flow) | covered | reprocess path = Phase 3 |
| 05-reconciliation | row counts / control totals / GL balance / FX completeness | reconciliation engine; `curated_build` gate | covered | |
| 05-reconciliation | hard gate blocks publish, no auto-retry | ADR-003; pipeline task table | covered | |
| 05-reconciliation | sub-ledger↔GL tie-out | reconciliation check, **warn-only initially** | partial | promote to hard check after 3 clean month-ends |
| 06-lineage-and-governance | column-level lineage | OpenLineage (ETL + dbt) → DataHub; row-level `_source_run_id` | covered | |
| 06-lineage-and-governance | 7-year audit retention | `RUN_MANIFEST` + S3 + log retention (arch-overview §4, component-design) | covered | |
| 06-lineage-and-governance | data contracts / change mgmt | contract-PR process (req 06); schema-drift check component | covered | process, not code |
| 07-scheduling-and-orchestration | Airflow/MWAA, per-source + curated_build | ADR-004; pipeline blueprint (both DAGs) | covered | |
| 07-scheduling-and-orchestration | CURATED ready by 06:00 CET | SLA chain (pipeline blueprint); ExternalTaskSensor gating | covered | |
| 07-scheduling-and-orchestration | retries, backfill, alerts | pipeline "Policies" + "Alert points" | covered | |
| 08-security-and-compliance | full PAN never persists | card parser drops PAN in memory (ADR-001, component-design) | covered | |
| 08-security-and-compliance | PII tokenised before Snowflake | PII tokeniser component; restricted load path | covered | |
| 08-security-and-compliance | `CURATED_SENSITIVE` row-access | ADR-005; ER `CUSTOMER_SENSITIVE` | covered | |
| 08-security-and-compliance | secrets by reference, KMS at rest | secrets resolver (component-design); SSE-KMS / Tri-Secret (arch-overview §4) | covered | |
| 08-security-and-compliance | GDPR erasure via crypto-shred | ADR-005 consequences; req 08 process | covered | UAT evidence pending (Q4 resolved in principle) |
| 09-non-functional | dev/uat/prod isolated, CI/CD | arch-overview §3; GitHub Actions + Terraform | covered | |
| 09-non-functional | observability / "healthy" definition | observability component; health dashboard | covered | |
| 09-non-functional | RPO 24h / RTO 8h | re-extractable sources (35d), Time Travel, manual reg fallback | covered | |
| 09-non-functional | data stays in EU, eu-central-1 only | all components in `eu-central-1`; egress proxy allowlist | covered | |

## Gaps

| Requirement not covered | Why | Proposed follow-up |
|-------------------------|-----|--------------------|
| Final BCBS 239 mandatory-field constraints (Q1) | list not yet delivered | add `not_null` tests + model columns when Regulatory Reporting delivers the list; blocks go-live sign-off, not design |
| Sub-ledger↔GL tie-out as a hard check | reconciling items expected until manual journals removed | keep warn-only; promote after 3 clean month-ends |
| Quarantine reprocessing / drain workflow | that is Phase 3 (build) scope | design `reprocess` task in Phase 3 |
