# CI/CD plan

> Phase 4 deliverable. The pipelines that lint, test, plan, apply and promote.
> Derived from `design/deployment-and-iac.md` s.4-5. This file is the concrete
> workflow spec; scaffold the workflow files from it.

- **CI/CD tool:** GitHub Actions / GitLab CI / Azure DevOps / ...
- **Runners:** hosted / self-hosted (why)
- **Cloud auth:** OIDC federation (no stored keys) / stored secrets

## Workflows

### `pr.yml` - on pull request

| Job | Steps | Gate |
|-----|-------|------|
| lint | formatter, `sqlfluff`, `tflint`, `terraform fmt -check` | must pass |
| unit | Phase 3 `<task> test` (unit + `dbt build --target ci` on DuckDB) | must pass |
| dbt slim build | `dbt build --select state:modified+ --defer --state <prod manifest>` on a CI schema | all tests green |
| tf plan | `terraform plan` per env, posted as a PR comment | no un-labelled destroy of a stateful resource |
| security | dependency + secret scan (Phase 5 adds SAST/IaC scan) | no criticals |

### `main.yml` - on merge to `main`

1. `terraform apply` (dev) -> 2. `dbt build --target dev` -> 3. deploy
   orchestrator code (dev) -> 4. post-deploy smoke (`dbt build --select
   tag:canary`, freshness).

### `promote.yml` - manual / tag

- Environment `test`: manual approval -> apply + `dbt build --target test` +
  deploy -> smoke.
- Environment `prod`: manual approval (N reviewers) + change-window check ->
  apply + `dbt build --target prod` + deploy -> smoke -> `git tag vX.Y.Z`.

## Promotion rules

- Promote the **exact git SHA + dbt `manifest.json`** - never rebuild per env.
- Per-env difference = `<env>.tfvars` + `dbt --target <env>` + env config only.
- `hotfix`-labelled PRs may bypass the change window (still need approvals).

## Secrets & auth

| Secret | Where | Consumed by |
|--------|-------|-------------|
| cloud role | OIDC, per env | tf apply, dbt, deploy |
| warehouse token / key | CI env secret, per env | dbt |
| orchestrator deploy token | CI env secret | deploy job |

No secret **values** in the repo; references only.

## Branch protection (handed to `git-workflow.md`)

Required checks: `lint`, `unit`, `dbt slim build`, `tf plan`. Linear history,
1+ review, CODEOWNERS on `infra/` and `.github/`.

## Skeleton files to scaffold

`.github/workflows/{pr,main,promote}.yml` (or the tool equivalent) - jobs and
steps named, `needs:` wired, environments referenced, secrets as `${{ }}`
references. Commands are real; account-specific values are `TODO`.
