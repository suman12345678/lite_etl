# Git workflow - Northwind Commerce (DEMO)

> Phase 4 deliverable. How changes flow from a branch to production.

- **Repo:** `github.com/northwind/northwind-data` (mono-repo)
- **Default branch:** `main`
- **Model:** **trunk-based** - short-lived branches, squash merge, linear history. - `10`

## Branches

| Branch | Purpose | Deploys to |
|--------|---------|-----------|
| `main` | always releasable; every merge auto-deploys **dev** | dev (auto, `main.yml`) |
| `feature/<ticket>-<slug>` | one change; PR into `main` | CI only (`pr.yml`) |
| `hotfix/<ticket>-<slug>` | urgent prod fix; PR into `main`, PR labelled `hotfix` | fast-track promote (skips change window) |
| tag `vMAJOR.MINOR.PATCH` | a prd release, cut from `main` after stg healthy 24h | prd (via `promote.yml`) |

No long-lived `develop` / release branches. Backfill / experiment work uses
`feature/*` and is promoted the same way.

## Pull requests

- Small, one concern. Description links the requirement (`requirements/NN`) or
  design item (`design/…`, ADR-00N) it implements.
- **Required checks (branch protection):** `lint`, `unit`, `dbt-slim`,
  `tf-plan`. - `cicd-plan.md`
- **Reviews:** 1+ approval; **2** for changes under `infra/` or
  `.github/workflows/` (CODEOWNERS-enforced). Stale approvals dismissed on new
  commits.
- **Merge:** **squash**, linear history required. No merge with a red check or an
  unresolved `tf-plan` destroy (needs the `destroy-ok` label + a platform
  reviewer).
- Admins cannot bypass on `main`.

## Pre-commit hooks (`.pre-commit-config.yaml`)

| Hook | Does |
|------|------|
| `ruff` + `ruff-format` | Python lint + format |
| `sqlfluff-lint` (`files: ^dbt/models/`) | dbt SQL lint |
| `terraform_fmt` + `terraform_validate` + `tflint` | infra format + lint (`infra/`) |
| `gitleaks` + `detect-secrets` | block secrets / credentials |
| `end-of-file-fixer`, `trailing-whitespace`, `check-added-large-files`, `check-yaml`, `check-merge-conflict` | hygiene |
| `dbt parse` (local hook, manual stage) | catch broken `ref()` / `source()` early |

`make setup` runs `pre-commit install`. Phase 4 adds the `terraform_*` and
`detect-secrets` / hygiene hooks to the Phase 3 seed.

## Versioning & releases

- **SemVer** on prd releases; tag cut from `main` inside `promote.yml` after the
  prd apply + smoke succeed.
- Release notes auto-generated from merged PR titles + labels since the last tag.
- The promoted artefact is the **tag's SHA + its dbt `manifest.json`** (the
  `main.yml` build artifact), reused unchanged through stg and prd.
- Rollback = re-run `promote.yml` with an earlier tag's SHA (see
  `deployment-and-iac.md` s.6 for the data-side steps).

## CODEOWNERS

```
*                        @northwind/data-eng
/dbt/                    @northwind/analytics-eng
/dbt/seeds/              @northwind/analytics-eng @northwind/data-eng
/extractors/             @northwind/data-eng
/recon/                  @northwind/data-eng
/publish/                @northwind/data-eng
/northwind_dagster/      @northwind/data-eng
/infra/                  @northwind/data-platform
/.github/                @northwind/data-platform
/config/                 @northwind/analytics-eng @northwind/data-eng
```

## First push

1. Seed the repo from `<WS>/build/repo/` (Phase 3 scaffold + Phase 4 additions)
   as the initial commit on `main`:
   `chore: seed northwind-data from lite-etl-design phases 1-4`.
2. Apply `infra/bootstrap` then `infra/envs/dev` with `infra/modules/ci` so the
   `northwind-dev-ci` OIDC role exists (see `iac-plan.md` apply order).
3. Set branch protection on `main`: required checks above, linear history,
   squash-only, 1+ review (CODEOWNERS), no admin bypass.
4. Create GitHub Environments: `dev` (no reviewers), `stg` (1 reviewer), `prd`
   (2 reviewers from `@northwind/data-platform`, Tue/Thu deployment window).
5. Add Environment secrets per `cicd-plan.md` "Secrets & auth".
6. Register the self-hosted runners on the ECS cluster with labels
   `[self-hosted, northwind, <env>]`.

Pushing the repo, applying Terraform and configuring GitHub are **human steps
outside this harness**.
