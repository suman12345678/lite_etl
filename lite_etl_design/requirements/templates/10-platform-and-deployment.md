# 10 - Platform, transformation framework & deployment

> Phase 1 deliverable. How the harness stays portable across warehouses, how
> transformations are authored and tested, and how everything is provisioned and
> shipped. Unknowns -> `TBD - see 99-open-questions.md (Q<n>)`.

## Warehouse / engine portability

- **Target engine(s):** Snowflake / Databricks / BigQuery / Redshift / Synapse /
  DuckDB (local) / other - list every engine that must be supported
- **Single engine or multi-engine?** one now / one now but must stay swappable /
  genuinely multi (same models run on >1 engine)
- **Portability requirement:** must transformation SQL avoid engine-specific
  syntax? yes / no / where practical
- **Abstraction mechanism:** dbt adapter per engine / warehouse-agnostic SQL
  dialect (e.g. SQLGlot) / one hand-written codebase per engine / not required
- **Known engine-specific features relied on:** (MERGE, clustering, `QUALIFY`,
  Delta `MERGE`, `COPY INTO`, streams/CDC, geospatial, ...)

## Transformation framework

- **Tool:** dbt Core / dbt Cloud / SQLMesh / native SQL scripts / Spark /
  other - and version
- **Adapter(s):** `dbt-snowflake` / `dbt-databricks` / `dbt-bigquery` /
  `dbt-redshift` / ...
- **Repo / project layout:** mono-repo vs dedicated transform repo; one dbt
  project vs project-per-domain
- **Model layers:** staging -> intermediate -> marts (or bronze/silver/gold) -
  name the convention and what lives in each
- **Materialisations:** view / table / incremental / ephemeral - default and the
  per-layer policy; incremental strategy (`merge` / `insert_overwrite` /
  `append`) and `unique_key`
- **History / SCD2:** dbt snapshots / `dbt_utils` / hand-rolled - which entities
- **Tests:** built-in (`not_null`, `unique`, `accepted_values`,
  `relationships`) + packages (`dbt_utils`, `dbt_expectations`, `elementary`) +
  singular tests; which run in CI vs per-run
- **Packages / macros:** `dbt_utils`, `dbt_expectations`, `codegen`, `audit_helper`,
  Elementary, project macros
- **Seeds:** small reference CSVs managed in the repo? which
- **Docs / exposures:** `dbt docs` published where; downstream exposures declared
- **Sources & freshness:** `sources.yml` per landing dataset; `dbt source
  freshness` thresholds

## Infrastructure as Code

- **Tool:** Terraform / OpenTofu / Pulumi / AWS CDK / CloudFormation / Bicep /
  none (click-ops) - and version
- **What IaC manages:** warehouse databases/catalogs & schemas, roles/grants,
  virtual warehouses/compute, storage buckets & external locations, secret
  scopes/stores, network (PrivateLink/VPC), the orchestrator infra, CI runners,
  monitoring
- **What is *not* in IaC:** (dbt-managed objects, data, manual break-glass)
- **Providers / modules:** `snowflake`, `databricks`, `aws`, `google`, `azurerm`,
  `dbtcloud`, ... ; own modules vs registry modules
- **State backend:** S3+DynamoDB / GCS / Azure Blob / Terraform Cloud / Spacelift -
  locking, encryption
- **Environment isolation:** workspace-per-env / directory-per-env / separate
  state files; variable files per env
- **Drift detection:** scheduled `plan` / Terraform Cloud / driftctl - cadence and
  who is alerted

## Deployment & release

- **CI/CD tool:** GitHub Actions / GitLab CI / Azure DevOps / Jenkins /
  dbt Cloud jobs / Dagster+CI
- **Pipeline stages:** lint (sqlfluff / tflint) -> unit (dbt build on a CI
  schema, `terraform validate`) -> `terraform plan` on PR -> review ->
  `terraform apply` + `dbt build` on merge -> promote
- **Promotion flow:** dev -> test/UAT -> prod; automatic vs manual approval per
  hop; what artefact is promoted (git SHA / dbt manifest / container image)
- **Versioning:** git tags / semver / `dbt` state comparison (`--defer` +
  `state:modified`) for slim CI
- **Rollback:** revert-and-redeploy / `terraform apply` previous SHA /
  warehouse time-travel / blue-green schema swap
- **Secrets in CI:** OIDC to cloud / stored CI secrets / vault - reference scheme
- **Manual gates:** who approves a prod apply; change-window rules

## Environment topology

| Env | Warehouse account / workspace | Catalog / database | Compute | Access |
|-----|-------------------------------|--------------------|---------|--------|
| dev | | | | |
| test / UAT | | | | |
| prod | | | | |

- **Naming scheme across envs:** (`<env>_` prefix / separate accounts / tags)
- **Network:** public / PrivateLink / VPC peering per env

## Assumptions

-
