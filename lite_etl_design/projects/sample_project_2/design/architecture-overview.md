# Architecture overview - Northwind Commerce (DEMO)

> Phase 2 deliverable. Written by `design-etl-architecture` from
> [`../requirements/`](../requirements/) on 2026-09-09. Every choice carries a
> "because <requirement>". Fictional client.

- **Project:** Northwind Commerce - Unified Retail Analytics Harness
- **Date / version:** 2026-09-09 / v1.0
- **Requirements baseline:** `requirements/00..10` v1.1, `99-open-questions.md`
  (2 answered, 3 assumptions carried)

## 1. Approach

- **ETL vs ELT:** **ELT** - because `03` (all business logic in dbt on
  Databricks) and `10` (dbt Core + `dbt-databricks`). Extractors only land raw
  data + do minimal parse/aggregate (POS CSV, Shopify JSON, GA4 rollup).
- **Processing style per source:** batch - `pos` event-triggered (S3 sensor),
  the rest cron - because `07` (same-day, no streaming) and `01` source
  capabilities.
- **Zone model:** `bronze` (immutable landed Delta, `_run_id` tagged) ->
  `silver` (dbt staging + intermediate: cleanse, dedupe, currency, identity) ->
  `gold` / `gold_pii` (dbt marts: dims via snapshots, incremental facts, aggs) -
  because `02` and `03`.
- **Orchestration:** **Dagster** (Cloud hybrid, ECS agent) with `dagster-dbt` -
  because `07` (team skill, asset checks for the recon gate, no Airflow).
- **Storage & formats:** inbound files as delivered in `s3://…-inbound`; Delta
  everywhere in the lakehouse; facts partitioned by date grain, `ZORDER` on the
  common join key - because `02` and `09` (scale, query cost).
- **Idempotency & replay:** `run_id` per source per business date in every
  `bronze` row; dbt incremental `merge` on `unique_key`; POS supersede by
  `file_etag`; watermark advances only after reconcile PASS + publish - because
  `02` and `01` (POS re-sends, re-run double counting).
- **Transformation framework:** dbt Core 1.8, `dbt-databricks`; layers
  `staging`(view) -> `intermediate`(ephemeral) -> `marts`(table / incremental);
  SCD2 via dbt snapshots - because `10` and `03`. Detail in
  [`transformation-design.md`](transformation-design.md).
- **Warehouse portability:** single adapter now, kept swappable - engine-specific
  SQL (`MERGE`, `OPTIMIZE ZORDER`, `QUALIFY`) confined to macros + model configs
  so a future `dbt-snowflake` swap is bounded - because `10`.
- **Infrastructure as Code:** Terraform 1.9, providers `databricks` / `aws` /
  `google`; S3+DynamoDB state, directory-per-env - because `10` ("if it's not in
  Terraform it doesn't exist"). Detail in
  [`deployment-and-iac.md`](deployment-and-iac.md).
- **Deployment & promotion:** GitHub Actions - PR runs lint + `dbt build`
  (slim CI) + `terraform plan`; merge applies dev; manual approvals promote
  dev -> stg -> prd with the same git SHA + dbt manifest - because `10` and `09`.

## 2. Component inventory

| Component | Responsibility | Technology | Because (requirement) |
|-----------|----------------|------------|-----------------------|
| Extractors (5) | pull each source, land raw + `manifest.json` in `bronze` | Python (JDBC, `requests`, boto3), BigQuery job for GA4 | 01 |
| Landing writer | atomic Delta write, `_run_id`/`_source_file` tagging, POS supersede | Databricks / Delta | 02 |
| dbt runner (transform + DQ) | `dbt build` staging/intermediate/marts + snapshots + tests | dbt Core + `dbt-databricks`, run by Dagster | 03, 04, 10 |
| Reconciliation engine | run the `05` checks, write `_reconciliation.json`, gate publish | singular dbt tests + a Python manifest-compare, exposed as a Dagster asset check | 05 |
| Publisher | swap validated `gold` into place, register in UC | Databricks SQL, Dagster asset | 02, 06 |
| Orchestrator | asset graph, schedules, S3 sensor, retries, backfills, asset checks | Dagster (Cloud hybrid) | 07 |
| Lineage / metadata | run manifests + dbt `manifest.json` + UC lineage -> dbt docs site + OpenLineage | dbt docs, UC, S3 | 06 |
| Secrets / security | resolve secret-scope refs, hashing salt, PII split, KMS | Databricks secret scopes over AWS Secrets Manager, UC row filter/mask | 08 |
| Observability | metrics, DQ dashboard, cost + freshness alarms, paging | Dagster, Elementary, CloudWatch, Databricks system tables, PagerDuty | 09 |
| State store | watermarks, run registry | Delta `_state.watermarks`, Dagster run storage | 02 |
| IaC / provisioning | Terraform modules: UC + grants, storage + KMS, Dagster ECS agent, GA4 SA, CI OIDC, alarms | Terraform 1.9 | 10 |
| CI/CD deploy | lint -> validate -> plan + slim `dbt build` -> apply + build + Dagster deploy -> promote | GitHub Actions (self-hosted runners) | 10, 09 |

## 3. Environments

`dev` / `stg` / `prd` = separate Unity Catalog catalogs (`northwind_<env>`);
`prd` in a dedicated locked AWS account and customer-managed VPC. Promotion moves
the exact git SHA + dbt `manifest.json` unchanged; `<env>.tfvars` + `dbt --target
<env>` are the only per-env differences. `dev` = masked 5% sample; `stg` = full
masked copy weekly; `gold_pii` synthetic below prd. (from `09`, `10`)

## 4. Cross-cutting concerns

- **Data quality:** dbt tests (generic + `dbt_expectations` + singular) run
  inside `dbt build`; fail the run at >0.5% quarantine or any error-severity
  test; Elementary for reporting + anomalies. (`04`)
- **Reconciliation:** row counts, per-channel GMV control totals, refund
  balancing, FX coverage, PII-leak check; a FAIL fails the Dagster `reconcile`
  asset check so `publish` never materialises. (`05`)
- **Lineage:** run manifests + dbt manifest + UC column lineage; any `gold` row
  traces to source `run_id`, inbound files, dbt model git SHA, and the recon
  report. (`06`)
- **Security:** hashed email/phone in `gold`, real PII only in `gold_pii` (UC row
  filter + column mask, `northwind_pii_readers`); SSE-KMS at rest; TLS in
  transit; OIDC in CI; crypto-shred RTBF. (`08`)
- **Observability:** rows in/out, freshness lag, reject rate, recon deltas,
  build duration, DBU spend vs budget; healthy = all ingest assets fresh +
  `curated_build` green + reconcile PASS + published < 06:00. (`09`)
- **Transformation & portability:** one dbt project, `bronze->silver->gold`
  layer model; engine-specific SQL isolated in macros - see
  [`transformation-design.md`](transformation-design.md). (`10`)
- **Deployment & IaC:** Terraform owns everything except Delta objects, secret
  values, and Dagster code; GitHub Actions promotes dev -> stg -> prd - see
  [`deployment-and-iac.md`](deployment-and-iac.md). (`10`, `09`)

## 5. Open design assumptions

| Ref (Q#) | Assumption | Impact if wrong |
|----------|------------|-----------------|
| Q2 | 24-month backfill for OLTP / Shopify / POS | ~1 TB + one weekend of larger compute; no structural design change |
| Q3 | Dagster Cloud hybrid (ECS agent) | fallback = Dagster OSS webserver+daemon on the same ECS cluster; `orchestrator/` Terraform module swap only, asset code unchanged |
| Q4 | `fct_wholesale_opportunity` at fulfillment grain | grain + the `wholesale` GMV reconciliation change; marked `partial` in the matrix |

## 6. Out of scope

Streaming / real-time; the Looker semantic model and the Braze reverse-ETL job
(consume `gold`); replacing Salesforce or the POS system; fuzzy identity
resolution. (from `00`)
