# CI/CD plan - Northwind Commerce (DEMO)

> Phase 4 deliverable. The pipelines that lint, test, plan, apply and promote.
> From `design/deployment-and-iac.md` s.4-5 and `10` "Deployment & release".
> This file is the concrete workflow spec; the scaffold implements it.

- **CI/CD tool:** **GitHub Actions** - `10`, ADR-002
- **Runners:** **self-hosted** on the same ECS cluster as the Dagster agent -
  they need VPC access to reach `prd` (`09` / `10`). `pr.yml` lint/unit jobs may
  use `ubuntu-latest`; anything that touches `stg`/`prd` uses
  `runs-on: [self-hosted, northwind, <env>]`.
- **Cloud auth:** **OIDC federation** - `permissions: id-token: write`, assume
  `arn:aws:iam::<acct>:role/northwind-<env>-ci`. No stored cloud keys. Databricks
  + Dagster deploy tokens are per-env **GitHub Environment secrets**. - `08`

## Workflows

### `pr.yml` - on `pull_request` to `main`

| Job | Steps | Gate |
|-----|-------|------|
| `lint` | `ruff check`, `sqlfluff lint dbt/models`, `terraform fmt -check -recursive`, `tflint` | must pass |
| `unit` | `make test` = `pytest` (unit, 80% cov on `extractors/ recon/ publish/`) + `dbt build --target ci` on DuckDB with seeds + fixtures | must pass |
| `dbt-slim` | `dbt build --select state:modified+ --defer --state $PRD_MANIFEST` against a throwaway CI schema in `northwind_dev`; upload Elementary report artifact | all dbt tests green |
| `tf-plan` | matrix `[dev, stg, prd]`: `terraform init` + `terraform plan -out` in `infra/envs/<env>`; post the plan as a PR comment | **no destroy of a stateful resource without a `destroy-ok` label** |
| `security` | `gitleaks`, `pip-audit` (Phase 5 adds `tfsec`/`checkov` + SAST) | no criticals |

`needs`: none between them - all run in parallel. Branch protection requires
`lint`, `unit`, `dbt-slim`, `tf-plan` (see `git-workflow.md`).

### `main.yml` - on push to `main` (after merge)

```
apply-dev      terraform apply -auto-approve   infra/envs/dev
   |
dbt-dev        dbt build --target dev --vars {business_date: <canary>, run_id: ci-<sha>}
   |
deploy-dagster-dev   dagster-cloud deployment ... (cloud_agent)  |  image push + ecs update (oss_selfhost)
   |
smoke-dev      dbt build --select tag:canary --target dev  +  dbt source freshness  +  assert reconcile asset check green
```

A failed `smoke-dev` **auto-rolls back dev** (re-`apply` + redeploy previous SHA)
and blocks promotion. - `deployment-and-iac.md` s.7

### `promote.yml` - `workflow_dispatch` (input: `sha`) / on tag `v*`

- **Environment `stg`** (`environment: stg`, 1 reviewer): `terraform apply` stg
  -> `dbt build --target stg` -> deploy Dagster stg -> smoke. Precondition: dev
  healthy, last dev run `reconcile` PASS.
- **Environment `prd`** (`environment: prd`, **2 reviewers** from
  `@northwind/data-platform`, Tue/Thu change-window check unless PR labelled
  `hotfix`): `terraform apply` prd -> `dbt build --target prd` -> deploy Dagster
  prd -> smoke -> `git tag vX.Y.Z` + release notes from merged PR titles.
  Precondition: stg healthy 24h.

The job re-uses the **exact `sha`** and its `dbt manifest.json` artifact from the
`main.yml` run - nothing is rebuilt per env.

### `drift.yml` - scheduled `cron: "0 3 * * *"`

Matrix `[dev, stg, prd]`: `terraform plan -detailed-exitcode` in
`infra/envs/<env>`. Exit code `2` (non-empty plan) -> post to
`#northwind-platform` Slack + `gh issue create`. - `deployment-and-iac.md` s.7

## Promotion rules

- Promote the **exact git SHA + dbt `manifest.json`** - never a per-env rebuild. - `09`
- Per-env difference = `<env>.tfvars` + `dbt --target <env>` +
  `config/<env>.yml` + Dagster deployment name only. No code differences.
- `hotfix`-labelled PRs bypass the Tue/Thu change window; they still need the 2
  prd approvers.
- No promotion to prd unless stg has been healthy for 24h (`smoke` green, last
  `reconcile` PASS).

## Secrets & auth

| Secret | Where | Consumed by |
|--------|-------|-------------|
| `northwind-<env>-ci` AWS role | OIDC, no value stored | `terraform apply`, `dbt`, `dagster` deploy |
| `DATABRICKS_HOST` / `DATABRICKS_TOKEN` | GitHub Environment secret, per env | `dbt build`, `warehouse` module |
| `DAGSTER_CLOUD_API_TOKEN` (or ECS deploy role) | GitHub Environment secret, per env | `deploy-dagster-<env>` |
| `GCP_GA4_SA_KEY` ref | Secrets Manager ARN in `config/<env>.generated.yml` | `ga4_extract` at runtime (not CI) |
| `PAGERDUTY_ROUTING_KEY`, `SLACK_WEBHOOK` | Environment secret | `observability` module, alert resource |

No secret **values** in the repo - references only. `gitleaks` in `pr.yml` and
pre-commit enforce it.

## Branch protection (handed to `git-workflow.md`)

Required status checks: `lint`, `unit`, `dbt-slim`, `tf-plan`. Linear history,
squash merges, 1+ review (2 for `infra/` and `.github/` via CODEOWNERS),
dismiss stale approvals, no bypass for admins on `main`.

## Skeleton files to scaffold (in `build/repo/.github/workflows/`)

`pr.yml`, `main.yml`, `promote.yml`, `drift.yml` - jobs and steps named,
`needs:` wired, `environment:` referenced, `permissions: id-token: write` set,
secrets as `${{ secrets.* }}` / `${{ vars.* }}` references. Commands are real;
account ids, role ARNs, workspace hosts and the prod manifest path are `TODO`.
