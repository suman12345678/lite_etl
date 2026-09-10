# CI gates - Northwind Commerce (DEMO)

> Phase 5 deliverable. What must be green to merge, to deploy, and to promote.
> Extends `pipeline/cicd-plan.md` (the `pr` / `main` / `promote` / `drift`
> workflows) with the hardening checks.

## Merge gate  (PR -> `main`; enforced by branch protection)

| Check | Job / tool | Blocking | New in Phase 5? |
|-------|-----------|----------|-----------------|
| format + lint | `pr.yml:lint` - `ruff`, `sqlfluff`, `terraform fmt -check`, `tflint` | yes | no |
| unit tests + coverage | `pr.yml:unit` - `make test`; add `--cov-fail-under=80` on `extractors/ recon/ publish/` | yes | **cov gate** |
| dbt slim build + data tests | `pr.yml:dbt-slim` - `dbt build --select state:modified+ --defer --state <prd manifest>` on a throwaway CI schema | yes | no |
| contract: `sources.yml` + `gold` schema | new `pr.yml:contract` - run C1-C4 (`integration-e2e-plan.md`); `gold_schema.json` snapshot diff | yes (unless `contract-change` label + consumer link) | **yes** |
| integration fast subset | new `pr.yml:integration` - `pytest -m integration -k "I1 or I4 or I5"` on dev | yes | **yes** |
| `terraform plan` (dev/stg/prd) | `pr.yml:tf-plan` - posted as a PR comment | yes - **no un-labelled destroy of a stateful resource** (`destroy-ok` label + platform review) | no |
| dependency scan | `pr.yml:security` - `pip-audit` | yes on **critical** (Phase 5 flips from `|| true` to failing) | **yes** |
| IaC scan | new `pr.yml:iac-scan` - `checkov -d infra` + `tfsec infra` | yes on **HIGH**; no public buckets, no `0.0.0.0/0` on data ports | **yes** |
| secret scan | `pr.yml:security` - `gitleaks` + `detect-secrets` | yes | no (pre-commit already) |

**Branch protection on `main`:** linear history, squash only, 1+ review (2 for
`infra/` + `.github/` via CODEOWNERS), stale approvals dismissed, no admin bypass,
all checks above **required**. (`git-workflow.md`, `09` merge gate.)

## Deploy gate  (merge -> dev, `main.yml`)

- Merge gate green **and**
- `terraform apply` (dev) exits clean, `config/dev.generated.yml` regenerated, **and**
- post-deploy canary green: `dbt build --select tag:canary --target dev` +
  `dbt source freshness --target dev` + last `reconcile` asset check = PASS.
- **On canary red:** `main.yml:smoke-dev` auto-rolls back dev to the previous SHA
  and **blocks promotion** (`deployment-and-iac.md` s.7).

## Promote gate  (`promote.yml`)

| To | Requires |
|----|----------|
| **stg** (Environment `stg`, 1 reviewer) | nightly E2E (E1, E3, E4, E5) green on `main` in the last 24h; dev healthy + last dev `reconcile` PASS; **same SHA + `_manifests/dbt/<sha>.json`** (no rebuild); manual approval |
| **prd** (Environment `prd`, 2 reviewers from `@northwind/data-platform`) | stg healthy **24h**; nightly E2E green; last `drift.yml` plan **empty** for all 3 envs; `security-review.md` signed off (no open high/critical); `runbook.md` reviewed; rollback plan linked in the PR; **Tue/Thu change window** (or PR labelled `hotfix`); manual approval x2 |

Promotion moves the **fixed git SHA + its dbt `manifest.json`** through stg and
prd unchanged; per-env difference is `<env>.tfvars` + `dbt --target <env>` +
`config/<env>.yml` only (`09`, `10`).

## Nightly / scheduled

| Job | Schedule | On failure |
|-----|----------|-----------|
| full integration (I1-I7) + E2E (E1-E8) on `main` | nightly | Slack `#northwind-data`; blocks next promotion |
| `drift.yml` - `terraform plan -detailed-exitcode` per env | nightly 03:00 UTC | issue + Slack `#northwind-platform`; blocks prd promote |
| `dbt source freshness` + `elementary` anomaly / DQ report | per scheduled pipeline run + a nightly digest | Slack digest; page only if in the error band |
| dependency + IaC scan (`pip-audit`, `checkov`) on `main` | nightly | issue; blocks promote on new critical/high |
| weekly whole-dataset `gold` hash check | weekly | issue (not a publish block) |

## What a failing gate does

- **Merge gate red** -> PR cannot merge; author fixes or gets a label + review
  for the two labelled exceptions (`contract-change`, `destroy-ok`).
- **Deploy canary red** -> auto-rollback dev to the previous SHA; promotion
  blocked; `#northwind-data` notified.
- **Promote gate red** -> promotion halts at that environment; on-call notified;
  no partial promote (stg can be healthy while prd is blocked - that is fine).
- **Nightly suite red** -> no new promotion until green again or the failure is
  triaged and explicitly waived by the on-call lead (recorded on the issue).

## Traceability

| Gate element | Requirement / source |
|--------------|----------------------|
| merge gate contents | `09` CI/CD; `pipeline/cicd-plan.md`; `git-workflow.md` |
| coverage 80% | `build/build-plan.md` s.4 |
| contract C1-C4, integration subset | `integration-e2e-plan.md` |
| IaC scan (no public buckets / open data ports) | `08` encryption + network; `security-review.md` F5-F6 |
| dependency scan fail-on-critical | `08` supply chain |
| promote prd preconditions | `deployment-and-iac.md` s.4-5; `10` "Manual gates" |
| drift check | `deployment-and-iac.md` s.7; `10` IaC |
