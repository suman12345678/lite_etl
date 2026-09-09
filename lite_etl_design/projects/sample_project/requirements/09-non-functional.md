# 09 - Non-functional requirements

> DEMO - fictional.

## Scale

- **Today:** 5 sources, ~30 curated tables, ~15 GB/day landed (~8M card rows the
  bulk of it)
- **Growth:** ~20% volume/year; +2-3 sources expected within 18 months
- **Peak:** go-live backfill of 13 months (~1.9 TB card history) - one-off,
  weekend, larger warehouse

## Performance

- **End-to-end latency:** T+1 batch. Business date D data lands overnight,
  CURATED published and signed off by **06:00 CET on D+1**
- **Per-pipeline runtime budget:** each source staged within its SLA window (see
  `07`); `curated_build` (dbt) < 60 min on a `MEDIUM` warehouse

## Cost

- **Budget:** Snowflake + AWS combined **< EUR 8,000 / month** in steady state
- **Controls:** Snowflake warehouses auto-suspend at 60s, right-sized per job
  (`XS` for extracts, `M` for dbt); S3 lifecycle to purge landing at 90 days;
  MWAA smallest viable environment class; monthly cost review

## Environments

- **dev / uat / prod** - separate AWS accounts and separate Snowflake accounts
- **Promotion:** all code + dbt + config in Git; promoted via tagged release
  through GitHub Actions; no manual changes in uat/prod
- **Test data:** UAT uses masked/tokenised production-like extracts; the
  tokenisation path is exercised in UAT (DPO-approved)

## CI/CD

- **On every PR:** config schema validation, Python unit tests, `dbt build` on a
  CI schema with `dbt test`, lineage manifest lint
- **Merge gate:** all of the above green + 1 review (2 for `CURATED` contract
  changes)
- **Deploy:** GitHub Actions -> tagged release -> Terraform for infra, image push
  for the ETL job, `dbt deploy` for models

## Observability

- **Logs:** structured JSON to CloudWatch (ETL) + Airflow task logs + dbt
  artifacts; 7-year retention for run-level records
- **Metrics:** rows in/out, bytes, duration, reject rate, freshness lag vs SLA,
  reconciliation pass/fail, warehouse credits per run
- **Dashboards:** one "Risk Data health" dashboard - DAG status, SLA burn-down,
  DQ score by feed, reconciliation status, cost to date
- **Healthy =** all DAGs green for the business date, every feed reconciled PASS,
  freshness > 30 min inside SLA, DQ score >= 0.995 on regulated feeds, MTD cost
  on track

## Resilience

- **RPO:** 24h - all sources are re-extractable for at least 35 days, so a lost
  day is recovered by re-running
- **RTO:** 8h for the pipeline platform; the 07:00 regulatory extract has a
  documented manual fallback for a single missed day
- **State store:** watermarks and run registry in Snowflake (`CURATED.PIPELINE_STATE`),
  covered by Time Travel + daily replication; S3 versioning on landing

## Tech constraints

- AWS `eu-central-1` only; prod AWS account is locked down (no public egress
  except via the proxy allowlist)
- Managed services preferred (MWAA, Secrets Manager, Snowflake); no self-hosted
  Kafka/Spark clusters
- Data must not leave the EU
