# 09 - Non-functional requirements

> DEMO - fictional. Platform, dbt and deployment specifics are in area 10.

## Scale

- **Sources / tables / volume today:** 6 sources; ~40 `gold` tables; ~2 TB total
  (Delta, compressed) growing to ~2.6 TB in 12 months.
- **Growth rate:** ~25% / year (store estate + online growth).
- **Peak load:** Black Friday / Cyber weekend - ~5x order volume; POS files
  larger and later; backfill-grade compute pre-provisioned for that window.

## Performance

- **End-to-end latency target:** a source change is visible in `gold` within
  **4 hours** on the normal cadence; the daily business date is fully published
  and reconciled by **06:00 UTC** (T+0 for POS/Shopify same-day close).
- **Per-pipeline runtime budget:** each ingest < 20 min; `curated_build` (dbt
  silver+gold + tests + reconcile) < 35 min on the standard job cluster.

## Cost

- **Budget:** Databricks + AWS + Dagster Cloud **< $6,000 / month** all-in.
- **Cost controls:** **job compute only** (no all-purpose clusters in
  automation); autoscaling 1-4 workers, spot with on-demand fallback;
  incremental models everywhere; `OPTIMIZE` + `VACUUM` weekly, not per run; GA4
  aggregated in BigQuery before extract; photon on for `curated_build` only;
  CloudWatch + Databricks system-tables cost alarm at 80% of budget.

## Environments

- **Environments:** `dev`, `stg`, `prd` - separate Unity Catalog catalogs;
  separate AWS accounts for `prd` (locked down), shared account for `dev`/`stg`.
- **Promotion flow:** git SHA + dbt `manifest.json` promoted unchanged dev ->
  stg -> prd; `<env>.tfvars` + `dbt --target <env>` the only differences
  (details in area 10).
- **Test data:** `dev` uses a masked 5% sample of prod (PII already hashed;
  `gold_pii` synthetic); `stg` uses a full masked copy refreshed weekly.

## CI/CD

- **On every change (PR):** `sqlfluff` lint, `dbt parse`, `dbt build
  --select state:modified+ --defer` on a CI schema, `terraform fmt`/`validate`/
  `tflint`/`plan`, Elementary report artifact.
- **Deployment mechanism:** GitHub Actions; merge to `main` = `terraform apply`
  + `dbt build` + Dagster deploy for `dev`; manual approvals to promote.
- **Merge gate:** all dbt tests green, no un-reviewed Terraform destroy of a
  stateful resource, 1 review, CI green.

## Observability

- **Logs:** Dagster run logs -> S3 + CloudWatch (13 months); dbt logs as run
  artifacts; extractor logs JSON to CloudWatch.
- **Metrics:** rows in/out per model, freshness lag per source, reject rate,
  reconciliation deltas, `curated_build` duration, DBU spend/day, cost vs budget.
- **Dashboards:** Dagster asset health; Elementary DQ dashboard; a Databricks
  SQL cost + freshness dashboard. "Healthy" = all ingest assets fresh for the
  business date, `curated_build` green, reconcile PASS, published before 06:00,
  spend on track.

## Resilience

- **RPO / RTO:** RPO 24h (all sources are re-extractable from the system of
  record or S3 inbound); RTO 4h.
- **Platform outage for a day:** sources retain data; on recovery, Dagster
  backfill the missed business dates oldest-first; consumers see a gap, not
  wrong data (nothing publishes without reconcile PASS).
- **State store durability:** Terraform state in S3 (versioned, SSE-KMS) +
  DynamoDB lock; watermarks in a Delta `_state.watermarks` table (Delta history
  = backup); weekly Delta **deep clone** of `gold` + `gold_pii` to `eu-west-2`.

## Tech constraints

- Approved services only: AWS + Databricks + Dagster Cloud + GitHub. No new SaaS
  without security review (Dagster Cloud pending - see Q3).
- `prd` network: Databricks in a customer-managed VPC, S3 via gateway endpoint,
  no public ingress; Postgres replica reached over VPC peering.
