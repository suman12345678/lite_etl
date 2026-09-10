# Git workflow

> Phase 4 deliverable. How changes flow from a branch to production.

- **Repo:**  - **Default branch:** `main`
- **Model:** trunk-based (short-lived branches) / GitFlow / ...

## Branches

| Branch | Purpose | Deploys to |
|--------|---------|-----------|
| `main` | always releasable; every merge deploys dev | dev (auto) |
| `feature/*` | one change; PR into `main` | CI only |
| `hotfix/*` | urgent prod fix; PR into `main`, labelled `hotfix` | fast-track promote |
| tag `vX.Y.Z` | a prod release | prod (via `promote.yml`) |

## Pull requests

- Small, one concern. Description links the requirement / design item.
- **Required checks:** `lint`, `unit`, `dbt slim build`, `tf plan` (from
  `cicd-plan.md`).
- **Reviews:** 1+ (2 for `infra/` and `.github/`), CODEOWNERS enforced.
- **Merge:** squash, linear history. No merge with a red check or an unresolved
  `tf plan` destroy.

## Pre-commit hooks (`.pre-commit-config.yaml`)

| Hook | Does |
|------|------|
| formatter | code + SQL formatting |
| `sqlfluff` | dbt SQL lint |
| `terraform_fmt` / `tflint` | infra lint |
| detect-secrets / gitleaks | block secrets |
| end-of-file / trailing-whitespace / large-file | hygiene |
| `dbt parse` (optional) | catch broken refs early |

## Versioning & releases

- **SemVer** on prod releases; tag from `main` after `test` is healthy.
- Release notes generated from merged PR titles / labels.
- The tag's SHA + its dbt `manifest.json` are the promoted artefact.

## CODEOWNERS

```
/dbt/            @org/analytics-eng
/extractors/     @org/data-eng
/infra/          @org/platform
/.github/        @org/platform
/<orchestrator>/ @org/data-eng
```

## First push

- Seed the repo from `<WS>/build/repo/` (Phase 3 scaffold + Phase 4 additions).
- Set branch protection on `main` with the required checks above.
- Enable environments (`dev` auto, `test` + `prod` with reviewers).
