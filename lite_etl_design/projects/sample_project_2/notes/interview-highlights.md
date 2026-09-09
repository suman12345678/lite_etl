# Interview highlights - Northwind Commerce (DEMO)

How the `/gather-requirements` interview ran on 2026-09-09. Kept as a record of
which points were multiple-choice (`AskUserQuestion`) vs prose, and every
"use your judgement" call that became an explicit assumption.

## Multiple-choice decision points (AskUserQuestion)

| # | Area | Question | Options offered | Answer |
|---|------|----------|-----------------|--------|
| 1 | 01 | `oltp` extract mode | full / incremental / CDC / file-arrival | incremental (`updated_at`, 60-min lookback) |
| 2 | 01 | `pos` delivery | SFTP / S3 object / API / DB | S3 object, file-arrival, S3 event -> sensor |
| 3 | 01 | `ga4` access | Lakehouse Federation / scheduled extract | *deferred -> Q1*, assumed extract |
| 4 | 02 | target platform | Snowflake / Databricks / BigQuery / Redshift | Databricks lakehouse (Unity Catalog, Delta) |
| 5 | 02 | `dim_customer` / `dim_product` load pattern | append / upsert / SCD2 / snapshot | SCD2 (via dbt snapshots) |
| 6 | 02 | big-fact load pattern | append / merge / insert-overwrite | incremental `merge` on `unique_key` |
| 7 | 03 | ETL or ELT | ETL engine / ELT in warehouse / mixed | ELT (dbt in Databricks); parse/aggregate only in extractors |
| 8 | 05 | reconciliation FAIL behaviour | block publish / alert only / auto-retry | block publish (blocking Dagster asset check) |
| 9 | 06 | lineage granularity | dataset / table / column | column-level for silver+gold |
| 10 | 07 | orchestrator | Airflow / Dagster / Prefect / cloud-native | Dagster (Cloud hybrid) - client vetoed Airflow |
| 11 | 10 | engine portability stance | LCD ANSI only / full multi-adapter / single adapter + isolate | single adapter now, isolate engine SQL in macros |
| 12 | 10 | transformation tool | dbt Core / dbt Cloud / SQLMesh / hand-SQL | dbt Core (run by Dagster + CI) |
| 13 | 10 | IaC tool | Terraform / OpenTofu / Pulumi / CDK / click-ops | Terraform 1.9, S3+DynamoDB state, dir-per-env |
| 14 | 10 | CI/CD promotion model | auto all the way / manual per hop / manual to prod only | auto to dev on merge, manual approval stg + prd (prd 2 approvers + change window) |

## Prose (open-ended) points

- **00** business goal, stakeholder map, success criteria (06:00 UTC publish,
  Shopify vs Finance GMV within 0.5%, no double-count on POS re-send).
- **01** per-source quirks: Shopify multi-currency + late partial refunds + test
  orders; POS cents + store-local timestamps + mid-day corrections; OLTP soft
  deletes + prior schema-drift incidents; GA4 cookie id is not a customer id.
- **03** identity match rule (hashed email or loyalty_id, source priority
  `oltp > shopify > salesforce`); currency conversion at `order_date` close
  rate; unknown-member (`_sk = -1`) rows.
- **04** DQ rule list per critical field; thresholds 0.5% fail / 0.1% warn.
- **05** control-total sources per channel (Shopify payout export, POS
  `totals.csv`, SFDC closed-won); tolerances.
- **08** PII field list + treatment (hash in gold, real in gold_pii); RTBF =
  crypto-shred; encryption standards.
- **10** repo layout (mono-repo with `dbt/ infra/ dagster/ extractors/`); dbt
  layer names + materialisation policy; Terraform module list + what is *not* in
  IaC; rollback approach per scenario.

## "Use your judgement" -> assumptions recorded

| Area | Point left to judgement | Assumption written down |
|------|-------------------------|-------------------------|
| 02 | landing file layout + retention | `s3://…-inbound/<src>/dt=…`; bronze 60d, gold 5y, gold_pii 25m |
| 03 | aggregate tables to build | `agg_sales_daily`, `agg_customer_monthly` |
| 04 | DQ reporting tool | Elementary dashboard + Slack digest + PagerDuty on failure |
| 07 | exact schedule times | ingests staggered 00-05:00 UTC; `curated_build` 05:15; publish by 06:00 |
| 09 | lower-env test data | dev = masked 5% sample; stg = full masked weekly; gold_pii synthetic |
| 10 | dbt package set | `dbt_utils`, `dbt_expectations`, `elementary`, `dbt_date`, `codegen` |
| 10 | Terraform state naming | `northwind-<env>-tfstate` + `northwind-tf-lock` DynamoDB |
| 10 | number of dbt projects | one project, domains as `marts/` subfolders (split only if build > 35 min) |

## Open questions raised (5)

Q1 GA4 federation vs extract *(answered same day: extract)*; Q2 backfill depth
12 vs 24 months; Q3 Dagster Cloud vs OSS on ECS; Q4 wholesale revenue-recognition
grain; Q5 `gold_pii` same catalog vs separate *(answered same day: same catalog,
UC-governed)*. See `../requirements/99-open-questions.md`.
