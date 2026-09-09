# Requirement -> design traceability matrix - Northwind Commerce (DEMO)

> Coverage proof. Every Phase 1 requirement file appears. Status: **covered** /
> **partial** / **deferred**.

| Req file | Item | Design element(s) that satisfy it | Status | Notes |
|----------|------|-----------------------------------|--------|-------|
| 00-project-brief | one trusted `gold`, reconciled by 06:00 UTC | architecture-overview s.1; pipeline-blueprint SLA chain; reconcile asset check | covered | |
| 00-project-brief | run cost < $6k/mo | design-decisions ADR-001/002/006; deployment-and-iac s.8; component `observability` cost alarm | covered | modelled, not yet validated on real volume |
| 00-project-brief | everything in Terraform | deployment-and-iac s.1-3; ADR-004 | covered | |
| 01-source-systems | `oltp` incremental + schema-drift | data-flow Shape A; component `extractor`; transformation-design s.3 (`sources.yml`) | covered | drift policy = fail |
| 01-source-systems | `shopify` multi-currency, partial refunds, test orders | int_sales__order_web; `to_usd` macro; stg_shopify filters | covered | |
| 01-source-systems | `pos` file-arrival + mid-day supersede | data-flow Shape B; `_file_etag` / `_superseded`; component `extractor` | covered | |
| 01-source-systems | `salesforce` Bulk incremental | data-flow Shape A; stg_sfdc__*; account_snapshot | covered | |
| 01-source-systems | `ga4` in BigQuery -> session grain | data-flow Shape C; `ga4_extract`; fct_web_session | covered | Q1 resolved (extract job) |
| 01-source-systems | `fx_rates` carry-forward | data-flow Shape D; dim_fx_rate; `to_usd` | covered | |
| 02-targets-and-loading | Databricks UC, bronze/silver/gold + gold_pii | architecture-overview s.1; data-entity-diagram; transformation-design s.2 | covered | |
| 02-targets-and-loading | SCD2 dims, incremental merge facts | transformation-design s.4-5; data-entity-diagram; snapshots | covered | |
| 02-targets-and-loading | idempotency per business date; watermark after PASS | pipeline-blueprint policies; component `extractor`/`publisher`; ADR-005 | covered | |
| 02-targets-and-loading | 24-month backfill | pipeline-blueprint backfill policy | partial | Q2: depth unconfirmed (12 vs 24) |
| 03-transformations | per-entity cleanse/standardise/dedup rules | transformation-design s.1-2; component `dbt runner`; data-flow checkpoints | covered | |
| 03-transformations | deterministic identity match | int_customer__resolved; `surrogate_key` macro; data-entity-diagram | covered | fuzzy match out of scope per 00 |
| 03-transformations | multi-currency -> USD at order_date | `to_usd` macro; dim_fx_rate; int_fx__daily | covered | |
| 03-transformations | wholesale revenue recognition | int_sales__order_wholesale; fct_wholesale_opportunity | partial | Q4: grain assumed = fulfillment |
| 04-data-quality | 7 dimensions as enforceable rules | transformation-design s.6; component `dbt runner`; data-flow DQ checkpoint | covered | rule table = `_models.yml` entries |
| 04-data-quality | 0.5% fail / 0.1% warn thresholds | singular reject-rate test; ADR-001 | covered | |
| 04-data-quality | Elementary reporting + anomaly | transformation-design s.6/8; component `observability` | covered | |
| 05-reconciliation | row counts, per-channel GMV, refund balancing, FX coverage, dupes, drift | transformation-design s.7 (`tests/recon_*`); component `reconciliation engine`; pipeline-blueprint gate | covered | wholesale GMV branch `warn` pending Q4 |
| 05-reconciliation | hard gate blocks publish | reconcile Dagster asset check; pipeline-blueprint; ADR-005 | covered | |
| 05-reconciliation | PII-leak check | `tests/assert_no_pii_in_gold.sql`; data-flow checkpoint | covered | |
| 06-lineage-and-governance | column-level lineage | architecture-overview s.4; transformation-design s.9 (dbt manifest + UC + OpenLineage); lineage columns in ER | covered | DataHub rollout out of scope |
| 06-lineage-and-governance | Unity Catalog + dbt docs glossary | transformation-design s.9; warehouse Terraform module | covered | |
| 06-lineage-and-governance | 5-year audit retention | deployment-and-iac (state/logs); 02 retention; component `publisher` (`_recon`) | covered | |
| 06-lineage-and-governance | schema-change / consumer contract | data-flow drift checkpoint; dbt exposures + 10-day notice | covered | |
| 07-scheduling-and-orchestration | per-source cadence + S3 sensor + SLA chain | pipeline-blueprint; component `orchestrator` | covered | |
| 07-scheduling-and-orchestration | Dagster, no Airflow | ADR-005; architecture-overview s.1 | covered | Cloud-vs-OSS = Q3 |
| 07-scheduling-and-orchestration | retries, backfill, alerting | pipeline-blueprint task table + policies | covered | |
| 08-security-and-compliance | hashed PII in gold, real in gold_pii | ADR-006; data-entity-diagram gold_pii; component `secrets & security` | covered | |
| 08-security-and-compliance | UC row filter + column mask, reader group | warehouse Terraform module; deployment-and-iac s.1 | covered | Q5 resolved |
| 08-security-and-compliance | crypto-shred RTBF | ADR-006; component `secrets & security` | covered | |
| 08-security-and-compliance | KMS at rest, TLS in transit, OIDC in CI | storage Terraform module; deployment-and-iac s.4; 09 | covered | |
| 09-non-functional | T+0 by 06:00, runtime budgets | pipeline-blueprint SLA chain; transformation-design s.4 | covered | |
| 09-non-functional | cost controls (job compute, OPTIMIZE weekly, incremental) | ADR-001; transformation-design s.4/8; component `observability` | partial | needs validation against real Black Friday volume |
| 09-non-functional | dev/stg/prd isolation + masked lower envs | deployment-and-iac s.3/8; architecture-overview s.3 | covered | |
| 09-non-functional | DR RPO 24h / RTO 4h | deployment-and-iac s.6; component `state store` (deep clone) | covered | |
| 10-platform-and-deployment | target engine / portability stance | architecture-overview s.1; ADR-003; transformation-design intro + s.8 | covered | |
| 10-platform-and-deployment | dbt layers / materialisation / snapshots / tests | transformation-design s.1-6 | covered | |
| 10-platform-and-deployment | Terraform scope + state backend + env isolation | deployment-and-iac s.1-3; ADR-004 | covered | |
| 10-platform-and-deployment | CI/CD stages, promotion, rollback | deployment-and-iac s.4-6; architecture-diagram deploy plane | covered | |
| 10-platform-and-deployment | environment topology | deployment-and-iac s.8; architecture-overview s.3 | covered | |

## Gaps

| Requirement not covered | Why | Proposed follow-up |
|-------------------------|-----|--------------------|
| Cost ceiling proven at peak (00, 09) | needs a load test / Black Friday dry-run on real volumes | Phase 5: run a backfill + a 5x-volume day on `stg`, compare DBU + S3 + Dagster spend to the $6k model |
| Wholesale GMV reconciliation (03, 05) | recognition grain unconfirmed (Q4) | Finance to confirm; then set `recon_gmv_control_total` wholesale branch to `severity: error` |
| Sub-day / intraday consumers | out of scope per 00 | none unless a consumer need emerges |
