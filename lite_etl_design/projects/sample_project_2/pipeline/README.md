# Phase 4 - Pipeline & Git - Northwind Commerce (DEMO)

> Index of the Phase 4 deliverables. Turns the Phase 3 components
> ([`../build/`](../build/)) and the Phase 2 design ([`../design/`](../design/))
> into runnable Dagster pipelines, a Terraform layout, and a GitHub Actions
> CI/CD flow. Plans and scaffolds only - no `terraform apply`, no deploy, no
> `git push`.

- **Project:** Northwind Commerce - Unified Retail Analytics Harness
- **Date / version:** 2026-09-09 / v1.0
- **Status:** drafted, pending review -> run `/validate-config`

## Files

| File | What it contains |
|------|------------------|
| [`repo-layout.md`](repo-layout.md) | The `northwind-data` mono-repo tree, ownership, generated-vs-authored, how `build/repo/` becomes the real repo. |
| [`orchestration-wiring.md`](orchestration-wiring.md) | `northwind_daily`: each design asset -> component call -> Dagster unit; the S3 sensor + cron schedules; retry policy; the reconciliation asset check; the backfill entrypoint; the skeleton file list. |
| [`iac-plan.md`](iac-plan.md) | The six Terraform modules + `bootstrap/`, per-module resource inventory (each traced to `deployment-and-iac.md`), S3+DynamoDB state backend, apply order, per-env variables, what IaC does not manage. |
| [`cicd-plan.md`](cicd-plan.md) | `pr` / `main` / `promote` / `drift` workflows: jobs, `needs:`, gates, promotion rules, OIDC auth, branch protection. |
| [`git-workflow.md`](git-workflow.md) | Trunk-based branch model, PR rules, pre-commit hooks, SemVer, CODEOWNERS, first-push steps. |
| [`environments-and-config.md`](environments-and-config.md) | dev/stg/prd matrix, the four-layer config model, promotion, drift detection, the config-keys inventory. |

## Scaffolded into `../build/repo/`

- `infra/bootstrap/` + `infra/modules/{warehouse,storage,orchestrator,ga4,ci,observability}/` + `infra/envs/{dev,stg,prd}/`
- `dagster/` code location - `assets/`, `checks/`, `resources.py`, `schedules.py`, `sensors.py`, `backfill.py`, `partitions.py`, `definitions.py`, `deployment.yaml`
- `.github/workflows/{pr,main,promote,drift}.yml`
- `CODEOWNERS`, extended `.pre-commit-config.yaml`, `config/<env>.generated.yml.example`

All skeletons: real structure, names, edges, retry config and the gate; `TODO` for
every account id / ARN / hostname / token / business rule the design does not pin.

## Open items carried into Phase 4

| # | Item | Handling in the scaffold |
|---|------|--------------------------|
| Q3 | Dagster Cloud hybrid vs OSS on ECS | `orchestrator/` module `var.mode` = `cloud_agent` (default) \| `oss_selfhost`; both paths stubbed. Asset code identical. |
| Q2 | Backfill depth 12 vs 24 months | `backfill.py` takes an explicit `[from, to]`; no structural impact. `TODO` note for the go-live window. |
| Q4 | Wholesale revenue-recognition grain | dbt-only; `curated_build` selection unchanged. Carried from Phase 3 O2. |

Phase 5 (`/harden-pipeline`) is next. Pushing the repo and running
`terraform apply` are human steps outside this harness.
