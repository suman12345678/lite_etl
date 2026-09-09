# Requirements - Northwind Commerce (DEMO)

**Project:** Northwind Commerce - Unified Retail Analytics Harness (fictional).
Land 6 source feeds into a governed **Databricks lakehouse**, transform with
**dbt**, provision and ship with **Terraform + GitHub Actions**, orchestrate with
**Dagster**, and publish a reconciled `gold` layer for Looker, Braze and the
Finance close by 06:00 UTC daily.

**Produced by:** the `gather-etl-requirements` skill (`/gather-requirements` then
`/finalize-requirements`) on 2026-09-09 from
[`../intake/northwind-commerce-discovery.md`](../intake/northwind-commerce-discovery.md).

| File | Headline |
|------|----------|
| [00-project-brief.md](00-project-brief.md) | one trusted sales/customer/margin view; gold reconciled by 06:00 UTC; < $6k/mo; everything in Terraform |
| [01-source-systems.md](01-source-systems.md) | 6 sources: Postgres OLTP (incremental), Shopify REST, POS CSV on S3 (file-arrival), Salesforce Bulk, GA4-in-BigQuery (extract), FX REST |
| [02-targets-and-loading.md](02-targets-and-loading.md) | Databricks UC, `bronze/silver/gold` + `gold_pii`; SCD2 snapshots, incremental `merge` facts, idempotent per business date |
| [03-transformations.md](03-transformations.md) | ELT; per-entity rules; multi-currency -> USD; POS supersede; deterministic identity match; unknown-member rows |
| [04-data-quality.md](04-data-quality.md) | 7 dimensions as dbt tests; 0.5% fail / 0.1% warn thresholds; Elementary reporting |
| [05-reconciliation.md](05-reconciliation.md) | row counts, GMV control totals per channel, refund balancing, PII-leak check; hard gate = blocking Dagster asset check |
| [06-lineage-and-governance.md](06-lineage-and-governance.md) | column-level lineage (run manifests + dbt manifest + UC lineage); Unity Catalog; 5-year audit |
| [07-scheduling-and-orchestration.md](07-scheduling-and-orchestration.md) | Dagster (Cloud hybrid, ECS agent); per-source schedules + S3 sensor; `curated_build` -> reconcile -> publish by 06:00 UTC |
| [08-security-and-compliance.md](08-security-and-compliance.md) | UK GDPR; hashed email in gold, real PII in `gold_pii` (UC row filter + mask); crypto-shred RTBF; SSE-KMS; OIDC in CI |
| [09-non-functional.md](09-non-functional.md) | ~2 TB, 25%/yr; T+0 by 06:00; job compute only; masked lower envs; DR RPO 24h / RTO 4h |
| [10-platform-and-deployment.md](10-platform-and-deployment.md) | Databricks now / kept swappable; dbt Core + `dbt-databricks`; Terraform 1.9 (S3 state, dir-per-env); GitHub Actions `plan/apply` + `dbt build` + manual dev->stg->prd promotion |
| [99-open-questions.md](99-open-questions.md) | 5 raised, 2 answered (GA4 extract; `gold_pii` same catalog), 3 carried into design |

**Open questions:** 5 (2 answered on 2026-09-09).
**Phase 1 status:** complete. Next: `/design-architecture`.
