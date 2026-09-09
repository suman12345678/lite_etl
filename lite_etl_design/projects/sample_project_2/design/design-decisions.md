# Design decisions (ADR log) - Northwind Commerce (DEMO)

> One record per load-bearing choice. Each links the requirement that forces or
> motivates it.

## ADR-001: ELT on Databricks with dbt, not an external ETL engine

- **Status:** accepted
- **Date:** 2026-09-09
- **Context:** `03` (all business logic as SQL), `10` (Databricks bought, team
  knows dbt), `09` (< $6k/mo, small team).
- **Options considered:**
  1. **ELT: land raw, transform with dbt in Databricks** - pros: one skill set,
     lineage + tests + docs built in, cheap (warehouse compute already paid
     for); cons: heavy pre-join logic is awkward in SQL.
  2. Spark/PySpark ETL jobs before load - pros: flexible; cons: second codebase,
     more compute, weaker lineage/tests, more to operate.
  3. A managed ELT tool (Fivetran/Airbyte) + dbt - pros: less extractor code;
     cons: per-row cost blows the budget, less control over CDC/superseding.
- **Decision:** ELT. Custom lightweight Python extractors land raw in `bronze`;
  **dbt** does everything from `silver` on.
- **Consequences:** one language (SQL) for transforms; DQ = dbt tests;
  portability work is bounded to macros. Pre-load logic limited to parse
  (POS/Shopify) and GA4 aggregation in the extractors.
- **Revisit if:** transform logic needs iterative/ML steps SQL can't express, or
  build time exceeds the 35-min budget.

## ADR-002: dbt Core (in Dagster + CI), not dbt Cloud

- **Status:** accepted
- **Date:** 2026-09-09
- **Context:** `07` (Dagster is the orchestrator, `dagster-dbt` integration),
  `10` (CI/CD in GitHub Actions), `09` (cost).
- **Options:** dbt Cloud (scheduler + IDE + CI) vs dbt Core invoked by Dagster
  and GitHub Actions.
- **Decision:** dbt Core. Dagster owns scheduling and the recon gate; dbt Cloud
  would duplicate both and add seat cost.
- **Consequences:** we manage `profiles.yml` injection and the docs site
  ourselves; full control of selectors and slim CI; no extra vendor.
- **Revisit if:** the team wants the dbt Cloud IDE/semantic layer and the seat
  cost fits the budget.

## ADR-003: Single dbt adapter now, portability confined to macros

- **Status:** accepted
- **Date:** 2026-09-09
- **Context:** `10` ("kept swappable", business has considered Snowflake) but a
  genuine multi-engine build now would cost time for no current benefit.
- **Options:** (1) write only lowest-common-denominator ANSI SQL; (2) full
  multi-adapter with per-engine CI; (3) single adapter, isolate engine-specific
  SQL.
- **Decision:** option 3. `dbt-databricks` today; `MERGE`, `OPTIMIZE ZORDER`,
  `QUALIFY`, `current_timestamp`, surrogate-key hashing all go through
  `macros/`; incremental strategy in `config()`.
- **Consequences:** a future `dbt-snowflake` swap touches `profiles.yml`, ~5
  macros, and incremental configs - estimated days, not months. `dbt-duckdb`
  already used for unit tests, which keeps the macros honest.
- **Revisit if:** a second engine becomes a live requirement (then add
  per-engine CI).

## ADR-004: Terraform for all infrastructure; dbt owns data objects

- **Status:** accepted
- **Date:** 2026-09-09
- **Context:** `10` platform-team rule ("not in Terraform = doesn't exist"),
  `09` (reproducible envs), `08` (KMS, secret scopes, UC governance).
- **Options:** Terraform vs Pulumi vs CDK vs click-ops.
- **Decision:** Terraform 1.9, S3+DynamoDB state, directory-per-env. Terraform
  manages UC catalogs/schemas/grants, `gold_pii` row filter + column mask,
  storage + KMS, the Dagster ECS agent, the GA4 GCP SA, CI OIDC, alarms. **dbt**
  owns tables/views/snapshots/seeds; **secret values** stay in Secrets Manager.
- **Consequences:** a clean split - no tool fights over Delta objects; every env
  is `terraform apply` + `dbt build`. Nightly drift plan catches console
  changes.
- **Revisit if:** the org standardises on Pulumi, or Terraform Cloud is adopted
  for state + policy.

## ADR-005: Dagster (Cloud hybrid) for orchestration; reconciliation as a blocking asset check

- **Status:** accepted (Cloud-vs-OSS pending Q3)
- **Date:** 2026-09-09
- **Context:** `07` (team has Dagster experience, client vetoed Airflow), `05`
  (hard recon gate), `06` (lineage).
- **Options:** Airflow/MWAA (rejected by client), Dagster Cloud hybrid, Dagster
  OSS self-hosted, Databricks Workflows only.
- **Decision:** Dagster with `dagster-dbt`; software-defined assets partitioned
  by business date; the reconciliation gate is a **blocking asset check** so
  `publish` cannot materialise on FAIL. ECS Fargate agent, provisioned by
  Terraform.
- **Consequences:** asset lineage in the Dagster UI complements dbt/UC lineage;
  backfills are first-class; the recon gate is enforced by the framework, not a
  convention. Databricks Workflows still runs the maintenance `OPTIMIZE`/`VACUUM`
  job.
- **Revisit if:** Q3 lands on OSS (swap the `orchestrator/` Terraform module
  `mode`, asset code unchanged) or Dagster Cloud pricing changes.

## ADR-006: Hashed PII in `gold`, real PII only in `gold_pii` (same catalog, UC-governed)

- **Status:** accepted
- **Date:** 2026-09-09
- **Context:** `08` (UK GDPR, small PII-reader group, crypto-shred RTBF), Q5
  (DPO approved same-catalog UC governance).
- **Options:** (1) separate catalog/workspace for PII; (2) same catalog, UC row
  filter + column mask; (3) tokenisation vault.
- **Decision:** option 2. `silver` hashes email/phone with a per-subject salt;
  `gold.dim_customer` carries only `email_hash` + non-identifying attrs;
  `gold_pii.dim_customer_pii` (same `customer_sk`) holds real values with a UC
  row filter (marketable-consent scope) + column mask + `northwind_pii_readers`
  grant. RTBF = drop the subject salt (crypto-shred) + delete `gold_pii` rows +
  tombstone `dim_customer`.
- **Consequences:** Marketing segments on `email_hash` without ever seeing PII; a
  singular `assert_no_pii_in_gold` test blocks publish if a raw field leaks; no
  second workspace to run.
- **Revisit if:** Legal later requires physical isolation, or a downstream needs
  reversible tokenisation.

---

## Open decisions (need a user answer)

| # | Decision | Options | Blocking? | Linked Q# |
|---|----------|---------|-----------|-----------|
| 1 | Dagster Cloud hybrid vs Dagster OSS on ECS | cloud_agent / oss_selfhost | no (module var; asset code same) | Q3 |
| 2 | Backfill depth 12 vs 24 months | 12 / 24 | no (runtime + cost only) | Q2 |
| 3 | Wholesale revenue-recognition grain | order / fulfillment / invoice | partially (fct grain + wholesale recon) | Q4 |
