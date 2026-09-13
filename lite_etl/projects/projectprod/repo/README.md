# projectprod

Subscription revenue analytics: **extract (billing/crm/ref) -> dbt (staging -> intermediate ->
marts) -> data-quality + reconciliation gate -> publish**, on DuckDB/SQLite locally or on
Databricks/Snowflake in prod. Built standalone by `etl-build-prod` from `../spec.md` +
`../design.md` -- this repo has both the local demo and the full production code in one pass.

## Quick start: the demo (no cloud, no credentials)

Needs **Python 3.10+** and `PyYAML` only.

    python -m venv .venv
    .venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
    pip install -r requirements.txt

    python -m demo.peek inputs         # BEFORE: source recipe, rules.yml, finance control total
    python -m demo.run                 # clean run  -> every check passes -> writes .local_state/gold/
    python -m demo.peek                # AFTER:  row counts, MRR, reconciliations, published gold/

    python -m demo.run --scenario fail # bad data -> rows quarantined + MRR identity BLOCKS publish, exit 1
    python -m demo.peek                # AFTER:  reject_fct_invoice populated, gold/ absent

(`make demo` / `make demo-fail` / `make peek-inputs` / `make peek` do the same if you have `make`.)

## What's here

| path | what |
|------|------|
| `demo/` | the runnable pipeline on stdlib **SQLite** -- `load.py` (synthetic sources), `sql/` (transforms, mirrored 1:1 by the dbt models), `rules.py` (runs `rules.yml`), `run.py` (orchestrates), `peek.py` (inspect in/out) |
| `rules.yml` | 5 quality checks + 2 reconciliations (revenue vs finance GL; MRR movement identity) -- `warn` / `quarantine` / `fail` / `block` |
| `extract/` | **real** extractor modules -- `billing.py` (REST, paginated, incremental by `updated_at`), `crm.py` (Postgres, full daily snapshot), `ref.py` (S3 CSV, full refresh). All credentials from env vars only. `extract/fixtures/` + `tests/` back the CI unit tests (no live creds needed). |
| `dbt/` | the **full** model set: `models/staging/` (5), `models/intermediate/` (2, MRR proration + spine), `models/marts/` (4: `dim_account`, `dim_plan`, `fct_invoice`, `fct_mrr_movement`) + `seeds/` + `tests/`. DuckDB `ci` target (real, seeded by `dbt/seed_ci_raw.py`) plus Databricks / Snowflake targets. |
| `publish/gate.py` | the real-warehouse counterpart of `demo/rules.py` + `demo/run.py`'s publish step: runs `rules.yml` against the marts `dbt build` just produced, publishes `gold/` + `_SUCCESS`, or blocks and exits 1. |
| `orchestration/` | the cron orchestrator: `run_daily.sh`, `run_hourly_land.sh`, `run_backfill.sh`, `crontab.txt` |
| `infra/` | Terraform: one module (`modules/pipeline`), `envs/dev` + `envs/prod`. Real resources: S3 landing bucket, IAM, ECS Fargate task defs + EventBridge schedules (the orchestrator, cloud form), and per-`engine` warehouse/catalog (Databricks SQL warehouse + Unity catalog/schema, or Snowflake warehouse + database/schema) |
| `.github/workflows/ci.yml` | lint · demo (clean + fail) · extractor unit tests (fixtures, no creds) · `dbt build --target ci` (full model set) · `terraform validate` |

## Real (live) run: env vars and tfvars you must set

Nothing in this repo contains a literal credential, hostname, or account id --
every one of these is read from `os.environ` or a Terraform `var.*`/tfvars entry.
`ENGINE` (`duckdb` | `databricks` | `snowflake`) selects the warehouse everywhere;
`dbt/profiles/profiles.yml`'s `--target` must match it (`ci` | `databricks` | `snowflake`).

### extract/billing.py -- billing.invoices, billing.subscriptions
- `BILLING_API_BASE_URL` -- the billing API's base URL
- `BILLING_API_TOKEN` -- bearer token (inject from Secrets Manager in prod)

### extract/crm.py -- crm.accounts
- `CRM_DB_HOST`, `CRM_DB_PORT`, `CRM_DB_NAME`, `CRM_DB_USER`, `CRM_DB_PASSWORD`

### extract/ref.py -- ref.plans, ref.fx_rates
- `REF_S3_BUCKET` -- bucket holding the hand-maintained/daily CSVs
- `REF_PLANS_KEY` (default `ref/plans.csv`), `REF_FX_RATES_KEY` (default `ref/fx_rates.csv`)
- AWS credentials via the normal AWS credential chain (IAM role in prod)

### Landing + gate (all extractors + publish/gate.py)
- `ENGINE` -- `duckdb` (default) | `databricks` | `snowflake`
- `RAW_SCHEMA` (default `raw`), `MARTS_SCHEMA` (default `marts`/`MARTS` per engine)
- `DUCKDB_PATH` -- when `ENGINE=duckdb`, the local/CI file path
- `DATABRICKS_HOST`, `DATABRICKS_HTTP_PATH`, `DATABRICKS_TOKEN` -- when `ENGINE=databricks`
- `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_PASSWORD`, `SNOWFLAKE_WAREHOUSE`,
  `SNOWFLAKE_DATABASE`, `SNOWFLAKE_SCHEMA`, `SNOWFLAKE_ROLE` -- when `ENGINE=snowflake`

### dbt (dbt/profiles/profiles.yml, non-`ci` targets)
- Databricks: `DBT_CATALOG`, `DBT_SCHEMA`, `DBT_DATABRICKS_HOST`, `DBT_DATABRICKS_HTTP_PATH`,
  `DBT_DATABRICKS_TOKEN` (fill from the matching `infra` output + Secrets Manager)
- Snowflake: `DBT_SNOWFLAKE_ACCOUNT`, `DBT_SNOWFLAKE_USER`, `DBT_SNOWFLAKE_PASSWORD` (or
  `DBT_SNOWFLAKE_AUTHENTICATOR=externalbrowser`/key-pair), `DBT_SNOWFLAKE_ROLE`,
  `DBT_SNOWFLAKE_DATABASE`, `DBT_SNOWFLAKE_WAREHOUSE`, `DBT_SCHEMA`

### infra/ (Terraform var.* -- see infra/envs/<env>/<env>.tfvars, every `REPLACE_ME` there)
- `engine` -- `duckdb` | `databricks` | `snowflake` (spec.md Open questions: prod engine not yet decided)
- `aws_region`, `landing_bucket_name`, `ecs_cluster_arn`, `vpc_subnet_ids`, `security_group_ids`,
  `pipeline_image_uri` -- your AWS account's values, never committed as real values
- `billing_api_token_secret_arn`, `crm_db_password_secret_arn`, `warehouse_secret_arn` -- Secrets
  Manager ARNs only; Terraform never reads or stores the secret *value*
- Provider auth for `databricks`/`snowflake` providers themselves comes from their own standard
  env vars (`DATABRICKS_HOST`/`DATABRICKS_TOKEN`, `SNOWFLAKE_ACCOUNT`/`SNOWFLAKE_USER`/...), not tfvars

## Run the full model set / real extractors / infra locally

    make dbt-ci        # seeds a DuckDB raw schema from the SAME demo fixture, then
                        # `dbt build --target ci` over the FULL model set (staging + intermediate + marts + tests)
    make test-extract  # extractor unit tests against extract/fixtures/, no live creds
    make tf-validate    # terraform validate (dev), no AWS credentials needed
    make deploy ENV=dev # terraform apply, once infra/envs/dev/dev.tfvars is filled in

## The point

The demo runs on SQLite so it starts anywhere with zero setup. `dbt/seed_ci_raw.py` seeds the
*same* deterministic fixture into DuckDB so `dbt build --target ci` exercises every staging,
intermediate, and marts model -- not a slice -- with numbers that reconcile the same way the demo's
do. `extract/*.py` are real REST/Postgres/S3 clients (pagination, incremental-by-`updated_at`,
retry-with-backoff) gated only by env vars, with fixture-backed unit tests so CI never needs live
credentials. `infra/` provisions real AWS (landing bucket, IAM, the ECS+EventBridge cron
orchestrator) plus whichever warehouse `engine` names -- flipping `engine` from `databricks` to
`snowflake` (or vice versa) touches no dbt model, no `rules.yml` rule, and no orchestration script.
