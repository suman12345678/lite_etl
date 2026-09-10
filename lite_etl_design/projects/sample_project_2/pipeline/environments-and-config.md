# Environments & config - Northwind Commerce (DEMO)

> Phase 4 deliverable. The environment matrix and how configuration is layered so
> the same artefact runs everywhere. From `requirements/09` + `10` and
> `design/deployment-and-iac.md` s.8.

## Environment matrix

| | dev | stg | prd |
|---|-----|-----|-----|
| Databricks workspace | `northwind-dev` (shared AWS acct) | `northwind-stg` (shared AWS acct) | `northwind-prd` (**dedicated locked AWS acct**) |
| UC catalog | `northwind_dev` | `northwind_stg` | `northwind_prd` |
| Compute | job compute, 1-2 spot workers | job compute, 1-4 workers | job compute 1-4 + **photon on `curated_build`** + on-demand backfill pool |
| Object storage | `northwind-dev-{inbound,lakehouse,dbt-docs}` | `northwind-stg-*` | `northwind-prd-*` |
| Orchestrator deployment | Dagster deployment `northwind-dev` (`mode=cloud_agent`) | `northwind-stg` | `northwind-prd` |
| Access | all engineers | engineers + release approvers | pipeline SP + named on-call + read-only consumers |
| Network | shared VPC, public control plane / private data plane | shared VPC | customer-managed VPC, **no public ingress**, S3 gateway endpoint, VPC peering to Postgres replica |
| Test data | synthetic fixtures / small masked sample | full masked copy | real |
| CI deploy | auto on merge to `main` | manual (1 approver) | manual (2 approvers + Tue/Thu window) |
| `dbt docs` | not published | not published | static S3 site behind Okta |

- **Naming across envs:** `northwind_<env>` catalog; `northwind-<env>-*` for AWS
  resources; identical schema/table names in every catalog. - `10`

## Config layering (lowest -> highest precedence)

1. **Defaults** - `config/defaults.yml` (safe everywhere): DQ + recon
   thresholds, per-source `lookback`/`page_size`, `obs` backend. Committed.
2. **Per-env overlay** - `config/<env>.yml` (`dev.yml` / `stg.yml` / `prd.yml`,
   plus `ci.yml` for local/DuckDB): `env`, `catalog`, storage URIs,
   `secrets.scope_prefix`, `lineage.namespace`. Committed.
3. **IaC outputs** - `config/<env>.generated.yml`, written by
   `terraform output -json | scripts/tf_to_config.py` after each env apply:
   resolved bucket URIs, ECS/ALB names, SNS topic ARNs, Databricks warehouse id,
   secret-scope names. **Generated - git-ignored**, rebuilt on every apply.
4. **Secrets** - resolved at runtime by reference only:
   `secret-scope://northwind/<env>/<src>#<field>` (Databricks secret scopes,
   values in AWS Secrets Manager). Never in any file. - `08`

Load order in `extractors/common/config.py`: `defaults` <- `<env>` <-
`<env>.generated` (deep-merge), then `secret-scope://` refs resolved lazily.
`dbt --target <env>` + `<env>.tfvars` + `config/<env>.yml` are the **only** knobs;
no code differs between envs. - `10`

## Promotion

The exact git SHA + dbt `manifest.json` move dev -> stg -> prd unchanged
(`cicd-plan.md`). A release is a `vX.Y.Z` tag; a rollback is re-deploying an
earlier tag's SHA. `config/<env>.generated.yml` is **not** promoted - each env
regenerates it from its own `terraform output`.

## Drift detection

- `drift.yml` runs `terraform plan -detailed-exitcode` per env nightly (03:00
  UTC); a non-empty plan posts to `#northwind-platform` and opens a GitHub issue. - `deployment-and-iac.md` s.7
- Post-deploy health: `dbt build --select tag:canary`, `dbt source freshness`,
  and the `reconcile` asset check green. A failed post-deploy check auto-rolls
  back dev and blocks promotion.

## Config keys inventory

| Key | Type | Layer | dev | stg | prd | Consumed by |
|-----|------|-------|-----|-----|-----|-------------|
| `env` | string | `<env>.yml` | `dev` | `stg` | `prd` | all |
| `catalog` | string | `<env>.yml` | `northwind_dev` | `northwind_stg` | `northwind_prd` | dbt, publisher |
| `storage.landing_uri` | string | `<env>.yml` / generated | `s3://northwind-dev-lakehouse/bronze` | ...stg... | ...prd... | landing writer, extractors |
| `storage.inbound_uri` | string | `<env>.yml` | `s3://northwind-dev-inbound` | ...stg... | ...prd... | pos S3 sensor |
| `storage.manifests_uri` / `storage.recon_uri` | string | `<env>.yml` | `.../_manifests`, `.../_recon` | ... | ... | landing, reconciliation |
| `secrets.scope_prefix` | string | `<env>.yml` | `northwind/dev` | `northwind/stg` | `northwind/prd` | secrets resolver |
| `secrets.pii_salt_ref` | secret ref | `<env>.yml` | `secret-scope://northwind/dev/pii#salt` | ...stg... | ...prd... | silver PII hashing, RTBF |
| `lineage.endpoint` | string | generated | TODO OpenLineage URL | TODO | TODO | lineage emitter |
| `lineage.namespace` | string | `<env>.yml` | `northwind_dev` | `northwind_stg` | `northwind_prd` | lineage emitter |
| `dq.fail_threshold_pct` / `dq.warn_threshold_pct` | number | `defaults.yml` | 0.5 / 0.1 | = | = | dbt tests |
| `recon.tolerance_pct` | number | `defaults.yml` | 0.5 | = | = | reconciliation gate |
| `recon.drift_warn_pct` / `recon.drift_fail_pct` | number | `defaults.yml` | 30 / 60 | = | = | reconciliation gate |
| `sources.<src>.lookback_minutes` / `.page_size` | number | `defaults.yml` | per source | = | = | extractors |
| `sources.pos.key_template` | string | `defaults.yml` | `pos/dt={date}/store={store}/txns.csv.gz` | = | = | pos extractor, S3 sensor |
| `sources.ga4.shard_lag_days` | number | `defaults.yml` | 2 | = | = | ga4 extract |
| `schedule.<pipeline>` | cron | `defaults.yml` (new) | see `orchestration-wiring.md` | = | = | Dagster schedules |
| `obs.metrics_backend` / `obs.log_level` | string | `defaults.yml` / `<env>` | `stdout` / `INFO` | cloudwatch / INFO | cloudwatch / INFO | obs |
| `warehouse.http_path` | string | generated | TODO (from TF) | TODO | TODO | dbt profiles, publisher |
| `orchestrator.deployment_name` | string | generated | `northwind-dev` | `northwind-stg` | `northwind-prd` | Dagster deploy |
| `alerts.pagerduty_routing_key` / `alerts.slack_channel` | secret ref / string | generated / `defaults` | ref / `#northwind-data` | ref / `#northwind-data` | ref / `#northwind-data` | alert resource |

`=` means "same as dev (from `defaults.yml`)".
