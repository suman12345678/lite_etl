# Repo layout

> Phase 4 deliverable. The tree the project ships in, and what lives where.
> Derived from `design/10-platform-and-deployment.md` (mono-repo vs split) and
> the Phase 3 `build/repo/` scaffold.

- **Project:**
- **Date / version:**
- **Repo model:** mono-repo / dedicated transform repo + infra repo / ...
- **Host:** GitHub / GitLab / ... - org / group

## Tree

```
<repo>/
  extractors/            # Phase 3 - one module per source
  dbt/                   # Phase 3 - staging / intermediate / marts / snapshots / seeds / macros / tests
  <orchestrator>/        # Phase 4 - dags/ or dagster/ or flows/ : pipeline definitions
  infra/                 # Phase 4 - Terraform modules/ + envs/{dev,test,prod}
  .github/workflows/     # Phase 4 - CI/CD (or .gitlab-ci.yml / azure-pipelines.yml)
  tests/                 # unit (3) + integration/contract/e2e (5) + fixtures + golden
  config/                # non-secret config, per-env overlays
  docs/                  # dbt docs build output, runbook (5), ADRs
  .pre-commit-config.yaml
  CODEOWNERS
  README.md  Makefile|justfile
```

## Ownership

| Path | Owner | Reviewers (CODEOWNERS) |
|------|-------|------------------------|
| `dbt/` | Analytics Eng | |
| `extractors/` | | |
| `infra/` | Platform | |
| `<orchestrator>/` | | |
| `.github/workflows/` | Platform | |

## Generated vs authored

| Generated (do not hand-edit) | Authored |
|------------------------------|----------|
| `dbt/target/`, `dbt` docs site, lockfiles | everything else |

## Promotion into the real repo

The Phase 3 `build/repo/` scaffold is the seed. Phase 4 either: (a) pushes
`build/repo/` as the initial commit of the real repo, or (b) copies it into an
existing repo path. Record which, and the first-commit / branch name here.
