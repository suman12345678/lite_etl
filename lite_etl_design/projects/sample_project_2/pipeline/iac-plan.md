# IaC plan - Northwind Commerce (DEMO)

> Phase 4 deliverable. The concrete Terraform layout to build, from
> `design/deployment-and-iac.md`. This file is the build order and resource
> inventory; the design file holds the rationale.

- **Tool & version:** **Terraform 1.9** (state in S3; OpenTofu accepted drop-in) - `10`, ADR-004
- **Providers (pinned):** `databricks ~> 1.50`, `aws ~> 5.60`, `google ~> 5.40`,
  `random ~> 3.6` - `deployment-and-iac.md` s.2
- **Registry modules:** `terraform-aws-modules/vpc/aws` (network lookups only)
- **Repo path:** `infra/`
- **Isolation:** directory-per-env, one state file per env, **no workspaces** - `09`

## Module tree

```
infra/
  bootstrap/                 # run once per AWS account - NO backend block
    main.tf variables.tf     #   S3 tfstate bucket (versioned, SSE-KMS CMK) + DynamoDB northwind-tf-lock
  modules/
    warehouse/               # UC catalog northwind_<env>, schemas bronze/silver/gold/gold_pii, grants,
                             #   gold_pii row filter (marketable-consent) + column mask + northwind_pii_readers group,
                             #   Databricks service principals, job compute policy
    storage/                 # S3 buckets (inbound, lakehouse, dbt-docs), lifecycle rules, SSE-KMS keys,
                             #   external locations + storage credentials
    orchestrator/            # var.mode = cloud_agent | oss_selfhost
                             #   ECS service + task role + ALB + SG + autoscaling; VPC lookups
    ga4/                     # GCP service account + BigQuery Data Viewer / Job User IAM bindings
    ci/                      # GitHub OIDC provider + role northwind-<env>-ci + runner instance profile
    observability/           # CloudWatch alarms (cost, freshness, SLA), SNS topics -> PagerDuty + Slack
  envs/
    dev/   backend.tf  main.tf  dev.tfvars
    stg/   backend.tf  main.tf  stg.tfvars
    prd/   backend.tf  main.tf  prd.tfvars
```

## Resource inventory (per module)

| Module | Key resources | From design ref |
|--------|---------------|-----------------|
| `bootstrap` | `aws_s3_bucket.tfstate` (+ versioning, SSE-KMS, public-access-block), `aws_kms_key.tfstate`, `aws_dynamodb_table.tf_lock` | deployment-and-iac s.3 |
| `warehouse` | `databricks_catalog.northwind_<env>`, `databricks_schema` x4 (`bronze/silver/gold/gold_pii`), `databricks_grants`, `databricks_sql_permissions`, `databricks_service_principal` (pipeline SP), `databricks_cluster_policy` (job compute), `gold_pii` row filter + column mask functions, `databricks_group.northwind_pii_readers` + membership | deployment-and-iac s.1-2; ADR-006 |
| `storage` | `aws_s3_bucket` x3 (`northwind-<env>-inbound`, `-lakehouse`, `-dbt-docs`), `aws_s3_bucket_lifecycle_configuration`, `aws_kms_key` (lakehouse CMK), `databricks_storage_credential`, `databricks_external_location` x N | deployment-and-iac s.1 |
| `orchestrator` | `data.aws_vpc` / `data.aws_subnets` lookups, `aws_ecs_service` (+ `aws_ecs_task_definition`), `aws_iam_role` (task + execution), `aws_lb` + `aws_lb_target_group` + `aws_lb_listener`, `aws_security_group`, `aws_appautoscaling_target`; `oss_selfhost` branch adds webserver + daemon services | deployment-and-iac s.2; `07`; ADR-005 |
| `ga4` | `google_service_account.ga4_reader`, `google_project_iam_member` (`roles/bigquery.dataViewer`, `roles/bigquery.jobUser`), `google_service_account_key` **ref only - TODO rotate via Secrets Manager** | deployment-and-iac s.1 |
| `ci` | `aws_iam_openid_connect_provider` (token.actions.githubusercontent.com), `aws_iam_role.northwind_<env>_ci` (trust = repo `northwind/northwind-data`, `ref:refs/heads/main` + env), least-privilege `aws_iam_policy`, runner `aws_iam_instance_profile` | deployment-and-iac s.4; `08` |
| `observability` | `aws_cloudwatch_metric_alarm` (cost 80% budget, source freshness, 06:00 SLA), `aws_sns_topic` + `aws_sns_topic_subscription` (PagerDuty https, Slack chatbot), `aws_cloudwatch_dashboard` | `09`; `pipeline-blueprint.md` alert points |

Every resource block in the scaffold carries a `# ref: <design section>` comment.

## State backend bootstrap

1. `cd infra/bootstrap && terraform init && terraform apply` **once per AWS
   account** (dev+stg share the shared account; prd is its own account). Creates
   `s3://northwind-<env>-tfstate` (versioned, SSE-KMS CMK) and DynamoDB
   `northwind-tf-lock`. No backend block - local state, committed nowhere; output
   the bucket/table names.
2. `infra/envs/<env>/backend.tf` points at
   `bucket = "northwind-<env>-tfstate"`, `key = "<env>/terraform.tfstate"`,
   `dynamodb_table = "northwind-tf-lock"`, `encrypt = true`.
3. One state file per env (dir-per-env). `prd` state lives in the dedicated
   locked `prd` AWS account. - `deployment-and-iac.md` s.3

## Apply order

1. `bootstrap` - once per account (state backend).
2. `ci` (OIDC) - so GitHub Actions can assume `northwind-<env>-ci`.
3. `storage` -> `warehouse` -> `orchestrator` -> `ga4` -> `observability`.
4. `terraform output` -> write `config/<env>.generated.yml` (bucket URIs,
   catalog, ECS/ALB names, SNS ARNs, secret-scope names).
5. Phase 3's `dbt build --target <env>` then creates Delta tables/views inside
   the provisioned `silver` / `gold` / `gold_pii` schemas.

`envs/<env>/main.tf` wires the modules in this order via `depends_on` where a
cross-module reference does not already force it.

## Per-env variables

| Variable | dev | stg | prd |
|----------|-----|-----|-----|
| `aws_account_id` / `aws_region` | shared acct / `eu-west-2` | shared acct / `eu-west-2` | **dedicated locked acct** / `eu-west-2` (TODO ids) |
| `databricks_workspace_host` | `northwind-dev` (TODO) | `northwind-stg` (TODO) | `northwind-prd` (TODO) |
| `catalog_name` | `northwind_dev` | `northwind_stg` | `northwind_prd` |
| `orchestrator_mode` | `cloud_agent` | `cloud_agent` | `cloud_agent` (Q3; `oss_selfhost` fallback) |
| `job_compute_min/max` | 1 / 2 (spot) | 1 / 4 | 1 / 4 + photon on `curated_build` + on-demand backfill pool |
| `network` | shared VPC, public control plane (TODO vpc id) | shared VPC (TODO) | customer-managed VPC, no public ingress, S3 gateway endpoint, Postgres peering (TODO) |
| `tfstate_retention_days` | 90 | 180 | 365 |
| `alarm_severity` / SNS target | Slack only | Slack + low-sev page | PagerDuty page + Slack |
| `dbt_docs_public` | false | false | behind Okta |

All values in `<env>.tfvars` are `TODO` placeholders or `var.` references - no
real account ids, ARNs, or hostnames in the scaffold.

## What IaC does NOT manage

(restated from `deployment-and-iac.md` so reviewers don't add them)

- Delta **tables / views / snapshots / seeds** - dbt owns these.
- Secret **values** - rotated in AWS Secrets Manager; Terraform manages only the
  Databricks secret **scopes + ACLs**.
- Dagster **asset / job / schedule / sensor definitions** - live in `dagster/`,
  deployed by CI.
- **Break-glass grants** - manual, time-boxed, logged.
- The Databricks **workspace + UC metastore** per env - platform team, upstream
  of this harness (deliberate click-ops).
- GitHub **repo settings / Environment reviewers** - repo admin.
- PagerDuty **escalation policy** - owned by SRE (Terraform wires the service
  endpoint only).

## Skeleton files to scaffold (in `build/repo/infra/`)

`infra/bootstrap/{main.tf,variables.tf,README.md}`,
`infra/modules/<name>/{main.tf,variables.tf,outputs.tf}` x6, and
`infra/envs/{dev,stg,prd}/{backend.tf,main.tf,<env>.tfvars}` - resource blocks
named and wired, `variable`/`output` declared, provider versions pinned, values
as `var.` refs or `TODO`. No real account ids, ARNs, or hostnames. Do not run
`terraform init`/`plan`/`apply`.
