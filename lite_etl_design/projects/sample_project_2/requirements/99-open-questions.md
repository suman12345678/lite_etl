# 99 - Open questions & assumptions

> DEMO - fictional. 5 raised; 2 answered same day via /finalize-requirements;
> 3 carried into design as explicit assumptions.

| Q# | Question | Why it matters | Interim assumption | Owner | Status |
|----|----------|----------------|--------------------|-------|--------|
| Q1 | GA4: Databricks Lakehouse Federation to BigQuery, or a scheduled BigQuery extract job to S3? | Federation avoids a copy but needs cross-cloud networking + broader GCP perms; affects area 01 + 10 | Scheduled extract job aggregating to session grain, Parquet to S3 inbound | Data Platform | **answered** |
| Q2 | Historical backfill depth for Shopify / OLTP / POS - 12 or 24 months? | Drives backfill compute + cost + go-live timeline; ~1 TB difference | 24 months | Finance | open |
| Q3 | Is Dagster Cloud (hybrid) approved by security, or must we self-host Dagster OSS on ECS? | Same asset code either way, but changes the Terraform `orchestrator/` module + support model | Dagster Cloud hybrid (agent on ECS) | InfoSec | open |
| Q4 | Wholesale revenue recognition for partial shipments - recognise at order, at fulfillment, or at invoice? | Changes `fct_wholesale_opportunity` grain + GMV reconciliation for the `wholesale` channel | Recognise at fulfillment | Finance | open |
| Q5 | Can `gold_pii` live in the same catalog with UC row filters + column masks, or does Legal require a separate catalog / workspace? | Separate workspace roughly doubles infra cost + operational load | Same catalog, UC row filter + column mask, `northwind_pii_readers` group | DPO / Legal | **answered** |

## Answered log

| Q# | Answer | Date | Answered by |
|----|--------|------|-------------|
| Q1 | Scheduled BigQuery extract job confirmed - platform does not want to open Databricks-to-BigQuery federation networking now. `ga4_extract` Dagster asset. | 2026-09-09 | Data Platform lead |
| Q5 | DPO approved same-catalog governance: UC row filter (marketable-consent scope) + column mask, dedicated reader group, all `gold_pii` access audited. | 2026-09-09 | DPO |

## Carried into design as assumptions (Phase 2 treats each as a design assumption)

- **Q2** - design and cost model assume **24 months** backfill; a weekend
  backfill window on a larger job cluster. If Finance says 12, halve the backfill
  estimate; no design change.
- **Q3** - design assumes **Dagster Cloud hybrid**; `deployment-and-iac.md` notes
  the OSS-on-ECS fallback (same asset code, Terraform swaps the agent for a
  Dagster webserver + daemon service).
- **Q4** - `fct_wholesale_opportunity` designed at **fulfillment grain** with a
  note; the `wholesale` GMV reconciliation check is `partial` until confirmed.
