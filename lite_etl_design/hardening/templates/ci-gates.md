# CI gates

> Phase 5 deliverable. What must be green to merge, to deploy, and to promote.
> Extends `pipeline/cicd-plan.md` with the hardening checks.

## Merge gate (PR -> `main`)

| Check | Tool | Blocking |
|-------|------|----------|
| format + lint | formatter, `sqlfluff`, `tflint`, `terraform fmt` | yes |
| unit tests | `<task> test` | yes |
| dbt slim build + tests | `dbt build --select state:modified+ --defer` | yes |
| data tests (generic + expectations) | `dbt test` | yes |
| contract: source + `gold` schema | schema snapshot diff | yes (unless `contract-change` label) |
| integration (fast subset) | `<task> test-integration` | yes or nightly |
| `terraform plan` | per env | yes - no un-labelled stateful destroy |
| dependency scan | `pip-audit` / `npm audit` / `trivy` | yes on criticals |
| IaC scan | `checkov` / `tfsec` | yes on high |
| secret scan | `gitleaks` | yes |

Branch protection: linear history, 1+ review (2 for `infra/`, `.github/`),
CODEOWNERS, all checks above required.

## Deploy gate (merge -> dev)

- Merge gate green + `terraform apply` (dev) clean + post-deploy canary
  (`dbt build --select tag:canary`, `dbt source freshness`) green.

## Promote gate (dev -> test -> prod)

| To | Requires |
|----|----------|
| test | nightly E2E green on `main`; manual approval; same SHA + manifest |
| prod | test healthy `<n>`h; E2E green; manual approval (N reviewers); change window (or `hotfix`); rollback plan linked; last drift plan empty |

## Nightly / scheduled

- Full integration + E2E suite on `main`.
- `terraform plan` drift check per env -> alert + issue on non-empty.
- `dbt source freshness` + Elementary/DQ anomaly report.

## Failing a gate

- Merge gate red -> PR cannot merge.
- Deploy canary red -> auto-rollback dev, block promotion.
- Promote gate red -> promotion halts, on-call notified.
