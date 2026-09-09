# Requirements - Meridian Trust Regulatory & Risk Data Harness (DEMO)

**Project:** governed T+1 batch pipeline landing 5 banking sources into Snowflake,
with data-quality and reconciliation controls gating a trusted `CURATED` layer
that feeds the 07:00 CET regulatory extract and Finance month-end close.

**Produced by:** the `gather-etl-requirements` skill (`/gather-requirements`) on
2026-09-03, from `../intake/meridian-trust-rfp-extract.md` plus an interview.
Refreshed by `/finalize-requirements` the same day after Q2 and Q4 were answered.

> Fictional client and data. This folder exists to demonstrate the
> lite-etl-design harness. See `../README.md` for the full how-it-was-used write-up.

## Files

| File | Area | Headline |
|------|------|----------|
| [00-project-brief.md](00-project-brief.md) | Brief | close 9d → 4d, zero re-filed submissions; Snowflake; EUR; SOX/BCBS 239/GDPR |
| [01-source-systems.md](01-source-systems.md) | Sources | Oracle core banking (incr.), card SFTP file (file-arrival), GL in BigQuery (snapshot), FX REST, SQL Server CRM (incr., PII) |
| [02-targets-and-loading.md](02-targets-and-loading.md) | Targets & loading | `RISK_DWH` RAW→STAGING→CURATED(+SENSITIVE); SCD2 dims, snapshot/append facts; idempotent per business_date |
| [03-transformations.md](03-transformations.md) | Transformations | ETL (Python) for parse/PII/tokenise; ELT (dbt) for model, SCD2, FX conversion |
| [04-data-quality.md](04-data-quality.md) | Data quality | 7 dimensions; fail regulated feed > 0.1% reject; GL debits==credits zero tolerance; quarantine not drop |
| [05-reconciliation.md](05-reconciliation.md) | Reconciliation | row counts, card TOTAL trailer, GL balance & tie-out, FX completeness; hard gate blocks publish |
| [06-lineage-and-governance.md](06-lineage-and-governance.md) | Lineage & governance | column-level lineage, OpenLineage→DataHub, 7-year audit, data contracts |
| [07-scheduling-and-orchestration.md](07-scheduling-and-orchestration.md) | Scheduling | Airflow on MWAA; per-source DAGs + `curated_build`; CURATED ready by 06:00 CET |
| [08-security-and-compliance.md](08-security-and-compliance.md) | Security | full PAN never persisted; FPE-tokenised PII; `CURATED_SENSITIVE` row-access; KMS; crypto-shred erasure |
| [09-non-functional.md](09-non-functional.md) | Non-functional | ~15 GB/day; < EUR 8k/month; dev/uat/prod isolated; GitHub Actions CI; RPO 24h / RTO 8h |
| [99-open-questions.md](99-open-questions.md) | Open questions | 5 raised, 2 answered (Q2 auto-publish, Q4 DPO erasure sign-off), 3 still open |

## Status

Phase 1 **complete**. 3 open questions carried forward as design assumptions.
Next: Phase 2 output in [`../design/`](../design/) (already produced in this demo).
