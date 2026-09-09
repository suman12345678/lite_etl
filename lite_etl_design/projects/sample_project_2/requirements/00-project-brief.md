# 00 - Project brief

> DEMO - fictional. Version 1.1 (Q1, Q5 folded in on 2026-09-09).

- **Project name:** Northwind Commerce - Unified Retail Analytics Harness
- **Date / version:** 2026-09-09 / v1.1
- **Prepared with:** Head of Data, Analytics Eng lead, Finance systems analyst,
  Platform engineer (interview 2026-09-09)

## Business goal

Northwind sells through 60 stores, a Shopify online store, and a B2B wholesale
arm, but has no single trusted view of sales, customers, or margin. Finance and
Marketing keep different numbers. This harness lands all six source feeds into a
governed Databricks lakehouse, applies data-quality and reconciliation controls,
and publishes a trusted `gold` layer that Looker, the Braze reverse-ETL, and the
Finance close all read from - same-day, reconciled, with column-level lineage.

## Stakeholders

| Role | Name / team | Interest |
|------|-------------|----------|
| Sponsor | VP Data & Analytics | one trusted number, faster close |
| Data owner(s) | Analytics Engineering | owns `silver` + `gold` models |
| Consumer(s) | Finance (close), Marketing (Braze segments), Merchandising (Looker) | reliable daily gold by 06:00 UTC |
| On-call / ops | Data Platform team | pipeline health, cost, Terraform |
| Governance | DPO / Legal | UK GDPR treatment of customer PII |

## Success criteria

- `gold` refreshed and **reconciled** every day by **06:00 UTC**; zero
  unreconciled publishes reach `gold`.
- Shopify vs Finance GMV agree within **0.5%** on the reconciliation report.
- POS mid-day corrections never double-count (idempotent re-load).
- Any `gold` figure traceable to source extract + run id + dbt model version.
- Run cost (Databricks + AWS + Dagster) **< $6,000 / month**.
- Every environment object exists in Terraform; no click-ops in prod.

## Scope

**In scope:**

- 6 sources: Postgres OLTP, Shopify REST, store POS CSV (S3), Salesforce,
  GA4-in-BigQuery, FX rates REST.
- Databricks lakehouse (Unity Catalog, Delta) with `bronze` / `silver` / `gold`
  + restricted `gold_pii`.
- dbt transformation project, Terraform IaC, Dagster orchestration, GitHub
  Actions CI/CD.
- DQ, reconciliation gate, column-level lineage, GDPR PII handling.
- 24 months historical backfill (Shopify, POS, OLTP).

**Out of scope:**

- Streaming / real-time (same-day batch only).
- The Looker semantic model and the Braze reverse-ETL job (client-owned;
  consume `gold`).
- Replacing Salesforce or the POS system.
- Identity resolution beyond deterministic email / loyalty-id match.

## Constraints

- **Timeline / milestones:** design sign-off Sep; MVP (OLTP + Shopify + POS ->
  gold sales) end Q4; all 6 sources Q1 next year.
- **Team skills / preferred stack:** Python, SQL, dbt, Dagster. No Airflow.
- **Budget / cost ceiling:** < $6k/month run cost.
- **Mandated platform or services:** Databricks (bought), AWS (incumbent),
  Terraform (platform-team rule), Unity Catalog for governance.

## Assumptions

- Same-day batch (T+0 by 06:00 UTC) satisfies every consumer; no intraday need.
- USD is the single reporting currency; FX converted at daily close rate.
- Databricks workspace + Unity Catalog metastore already provisioned per env by
  the platform team; this harness manages catalogs/schemas/grants downward.
- GA4 data is read via a scheduled extract job into `bronze` (Q1, resolved).
- `gold_pii` lives in the same catalog governed by Unity Catalog row filters and
  column masks (Q5, resolved by DPO).
