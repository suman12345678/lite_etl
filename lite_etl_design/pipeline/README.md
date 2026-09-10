# pipeline/ (harness) - Phase 4 templates shared across all projects

This folder holds the **reusable** Phase 4 (Pipeline & Git) templates. It is part
of the harness, not part of any one project.

| Item | Purpose |
|------|---------|
| `templates/` | Blank shapes for each Phase 4 deliverable. The `assemble-etl-pipeline` skill copies these into a project's `pipeline/` folder and fills them, then scaffolds `infra/`, the orchestrator code, and `.github/workflows/` (or the chosen CI) skeletons inside `<workspace>/build/repo/`. |

## What Phase 4 produces (into `<workspace>/pipeline/`)

| File | Contents |
|------|----------|
| `repo-layout.md` | The full repo tree (mono-repo or split), what lives where, ownership, what is generated vs authored. |
| `orchestration-wiring.md` | Per pipeline: components -> orchestrator tasks/assets, schedule/sensor, dependencies, retries, the reconciliation gate wiring, the backfill entrypoint. |
| `iac-plan.md` | Terraform (or equivalent) module tree, resource inventory per module, apply order, state backend bootstrap, per-env tfvars. |
| `cicd-plan.md` | CI/CD workflows: triggers, jobs, stages, gates, the `plan/apply` + `dbt build` flow, environments & approvals, secrets via OIDC. |
| `git-workflow.md` | Branching model, PR rules, required checks, pre-commit hooks, CODEOWNERS, versioning/tags, release notes. |
| `environments-and-config.md` | Env matrix, config layering (defaults -> env -> secrets), promotion of the exact artefact, drift detection. |
| `README.md` | Index + one-line status + date. |

Plus scaffolded skeletons in `build/repo/`: `infra/modules/*`, `infra/envs/*`,
the orchestrator project (`dagster/` or `dags/` or ...), `.github/workflows/*.yml`.

Run `/assemble-pipeline` after Phase 3. `/validate-config` checks the wiring at
any time. See `../MAP.md`.
