# 10 - Platform, transformation framework & deployment

> DEMO - fictional. Version 1.1 (Q1 folded in).

## Warehouse / engine portability

- **Target engine(s):** Databricks (Delta Lake + Unity Catalog + Databricks SQL)
  on AWS. Single engine today.
- **Single engine or multi-engine?** one now, **kept swappable** - the business
  has flirted with Snowflake and wants the option. No requirement to run the
  same models on two engines simultaneously.
- **Portability requirement:** transformation SQL should stay ANSI where
  practical; engine-specific constructs are allowed but must be **confined to
  macros and model configs**, not scattered through model bodies.
- **Abstraction mechanism:** **dbt** with the `dbt-databricks` adapter today; a
  future `dbt-snowflake` swap should touch only: incremental strategy configs,
  a handful of macros (`optimize_table`, `current_timestamp`, `qualify_dedupe`),
  and `profiles.yml`.
- **Engine-specific features relied on:** Delta `MERGE` (dbt incremental),
  `OPTIMIZE ... ZORDER BY`, `QUALIFY`, Unity Catalog row filters / column masks,
  `RESTORE` / time-travel, `dagster-dbt` asset mapping.

## Transformation framework

- **Tool:** **dbt Core 1.8** (not dbt Cloud - runs inside Dagster via
  `dagster-dbt` and in CI).
- **Adapter(s):** `dbt-databricks` (1.8.x); `dbt-duckdb` in unit tests / local.
- **Repo / project layout:** mono-repo `northwind-data/` containing `dbt/`,
  `infra/` (Terraform), `dagster/` (orchestration), `extractors/` (Python). One
  dbt project, domains as subfolders under `marts/`.
- **Model layers:**
  - `staging/` - `stg_<src>__<entity>`, one per bronze object; rename, cast,
    light cleanse; **views**.
  - `intermediate/` - `int_<domain>__<step>`; joins, dedupe, currency
    conversion, business logic; **ephemeral**.
  - `marts/<domain>/` - `dim_*` / `fct_*` / `agg_*`; **table** for dims,
    **incremental (`merge`)** for large facts.
  - maps to lakehouse `bronze` (landed, not dbt) -> `silver` (staging +
    intermediate) -> `gold` / `gold_pii` (marts).
- **Materialisations:** default `view`; `intermediate` `ephemeral`; `dim_*`
  `table`; `fct_order`, `fct_order_line`, `fct_refund`, `fct_web_session`,
  `fct_wholesale_opportunity` `incremental` with `incremental_strategy='merge'`,
  `unique_key` per area 02, partitioned by the date grain; `agg_*` `table`
  rebuilt daily.
- **History / SCD2:** **dbt snapshots** (`snapshots/`) with `strategy='timestamp'`
  on `updated_at` for `customer`, `product`, `store`, `account`; the `dim_*`
  models read the snapshot.
- **Tests:**
  - built-in generic: `not_null`, `unique`, `accepted_values`, `relationships`
    on every key and enum (area 04);
  - `dbt_expectations` for ranges, regex, row-count, distribution;
  - `elementary` for anomaly detection + the DQ report;
  - **singular tests** (`tests/`) for the reconciliation checks (area 05) and
    the PII-leak check (area 08);
  - CI runs `dbt build --select state:modified+`; each scheduled run runs the
    full `dbt build` for the built selection.
- **Packages:** `dbt_utils`, `dbt_expectations`, `elementary`, `codegen`
  (dev-only), `dbt_date`.
- **Seeds:** `country_codes.csv`, `channel_map.csv`, `category_map.csv`,
  `store_master.csv`, `currency_list.csv` - owned per area 03, PR to change.
- **Docs / exposures:** `dbt docs generate` published to a static S3 site behind
  Okta; exposures declared for `looker_sales`, `braze_segments`,
  `finance_close`.
- **Sources & freshness:** `sources.yml` per bronze dataset with
  `loaded_at_field = _extracted_at`; `dbt source freshness` runs before
  `curated_build` - warn_after 6h, error_after 12h (tuned per source vs its
  cadence in area 07).

## Infrastructure as Code

- **Tool:** **Terraform 1.9** (HCP-free; state in S3). OpenTofu acceptable
  fallback.
- **What IaC manages:** Unity Catalog catalogs + schemas + grants + the
  `gold_pii` row filter/column mask + `northwind_pii_readers` group; external
  locations + storage credentials; S3 buckets (inbound, lakehouse, state,
  dbt-docs); KMS keys; Databricks service principals + job compute policies +
  secret scopes/ACLs; the **Dagster Cloud ECS agent** (VPC, ECS service, task
  role, ALB); the GA4 reader **GCP service account** + BigQuery IAM; the GitHub
  **OIDC role**; CloudWatch alarms + SNS/PagerDuty wiring.
- **What is *not* in IaC:** Delta tables / views / snapshots (dbt owns these);
  secret **values** (rotated in Secrets Manager); Dagster asset/job definitions
  (in `dagster/`, deployed by CI); break-glass grants (manual, time-boxed,
  logged).
- **Providers / modules:** `databricks`, `aws`, `google` providers (version
  pinned); own modules `warehouse/` (UC + grants), `storage/` (buckets + KMS +
  external locations), `orchestrator/` (Dagster ECS agent), `observability/`
  (alarms + PagerDuty), `ci/` (OIDC + runner perms). Registry modules for VPC.
- **State backend:** S3 bucket `northwind-<env>-tfstate` (versioned, SSE-KMS) +
  DynamoDB table `northwind-tf-lock`. One state file per env.
- **Environment isolation:** directory-per-env - `infra/envs/{dev,stg,prd}/`
  each with its own `backend.tf`, `main.tf`, `<env>.tfvars`. No workspaces.
- **Drift detection:** scheduled `terraform plan` nightly per env in GitHub
  Actions; a non-empty plan posts to `#northwind-platform` and opens an issue.

## Deployment & release

- **CI/CD tool:** **GitHub Actions** (self-hosted runners on the same ECS
  cluster as the Dagster agent for VPC access to `prd`).
- **Pipeline stages:**
  1. **PR:** `sqlfluff lint` (dbt) + `terraform fmt -check` + `tflint`;
     `dbt parse` + `terraform validate`;
     `dbt build --select state:modified+ --defer --state <prd manifest>` against
     a throwaway CI schema in `northwind_dev`;
     `terraform plan` per env (posted as a PR comment);
     Elementary report uploaded as an artifact.
  2. **Merge to `main`:** `terraform apply` (dev) -> `dbt build` (dev target) ->
     `dagster` code-location deploy (dev).
  3. **Promote:** manual approval (GitHub Environment `stg`) -> apply + build +
     deploy `stg`; manual approval + change-window check (GitHub Environment
     `prd`, 2 reviewers) -> apply + build + deploy `prd`.
- **Promotion flow:** dev (auto on merge) -> stg (manual) -> prd (manual + 2
  approvers + Tue/Thu change window). The **exact git SHA and its dbt
  `manifest.json`** are promoted; nothing is rebuilt per env.
- **Versioning:** `vMAJOR.MINOR.PATCH` tag on every prd release; release notes
  auto-generated from merged PRs; slim CI via dbt `state:modified`.
- **Rollback:**
  - bad dbt model - revert the PR, redeploy the previous SHA,
    `dbt build --full-refresh --select <affected>+`;
  - bad infra change - `terraform apply` the previous SHA;
  - bad publish already consumed - Delta `RESTORE gold.<table> TO VERSION AS OF
    <n>` / time-travel, then rebuild the business date;
  - worst case - deep-clone copy in `eu-west-2` promoted read-only while fixing.
- **Secrets in CI:** GitHub OIDC -> AWS role (`northwind-<env>-ci`), no stored
  cloud keys; Databricks + Dagster deploy tokens in GitHub Environment secrets,
  scoped per env.
- **Manual gates:** prd apply needs 2 approvers from `@northwind/data-platform`
  and must be inside the change window unless tagged `hotfix`.

## Environment topology

| Env | Databricks workspace | UC catalog | Compute | Access | Network |
|-----|----------------------|------------|---------|--------|---------|
| dev | `northwind-dev` (shared AWS acct) | `northwind_dev` | job compute, 1-2 workers, spot | all engineers | shared VPC |
| stg | `northwind-stg` (shared AWS acct) | `northwind_stg` | job compute, 1-4 workers | engineers + release approvers | shared VPC |
| prd | `northwind-prd` (dedicated locked AWS acct) | `northwind_prd` | job compute, 1-4 workers + photon on `curated_build`, backfill pool on demand | pipeline SP + named on-call + read-only consumers | customer-managed VPC, no public ingress, S3 gateway endpoint, VPC peering to Postgres |

- **Naming scheme across envs:** `northwind_<env>` catalog; `northwind-<env>-*`
  for AWS resources; identical schema/table names in every catalog.
- **Network:** dev/stg public control plane + private data plane; prd fully
  private.

## Assumptions

- Databricks workspaces + the UC metastore per env already exist (platform team);
  this harness's Terraform manages catalogs and everything below.
- Dagster Cloud (hybrid) is approved (Q3 - pending infosec; fallback: self-host
  Dagster OSS on the same ECS cluster, same asset code).
- One dbt project is sufficient; split to project-per-domain only if build time
  exceeds the 35-min budget.
