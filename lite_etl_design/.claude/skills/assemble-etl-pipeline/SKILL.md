---
name: assemble-etl-pipeline
description: Run Phase 4 of the ETL data-harness design process - wire the Phase 3 components into runnable pipelines for the chosen orchestrator, plan the Terraform/IaC and the CI/CD workflows, define the repo layout and git workflow, and scaffold infra/ + orchestrator + CI skeletons in the workspace's build/repo/. Use after components are built, or when the user runs "/assemble-pipeline".
---

# assemble-etl-pipeline  (Phase 4)

Take the Phase 3 components and the Phase 2 design and produce: a repo layout, the
orchestration wiring, an IaC plan, a CI/CD plan, a git workflow, and an
environments/config model - plus scaffolded `infra/`, orchestrator, and CI
skeletons. This skill plans and scaffolds; it does not run `terraform apply`,
deploy, or push anything.

## Step 0 - Resolve the workspace and check preconditions

1. Read `state/active-workspace` -> `<WS>`. If missing or `<WS>/project.json` is
   absent, tell the user to run `/etl-new-project` and stop.
2. Read `<WS>/progress.json`. If `phases.3_build_and_test.status` is not
   `complete` (or `in_progress` with a real `build/repo/` scaffold), stop and
   tell the user to run `/build-components` first.
3. Read `<WS>/design/` (especially `deployment-and-iac.md`, `pipeline-blueprint.md`,
   `architecture-overview.md`), `<WS>/requirements/10-platform-and-deployment.md`
   (repo model, canonical env names, CI/CD tool), and `<WS>/build/`
   (`build-plan.md`, the buildsheets, `dbt-project-scaffold.md`). List
   `<WS>/build/repo/` and confirm it contains `dbt/dbt_project.yml`, at least one
   extractor module, a task-runner file and the `demo/` walking skeleton; if not,
   stop and tell the user to finish `/build-components`.
4. Skim the harness `pipeline/templates/`.
5. `mkdir -p <WS>/pipeline/`.

## Step 1 - Settle the assembly choices

- **Repo model** - mono-repo vs split, host, from `requirements/10-platform-and-deployment.md`.
- **Environment list** - use the canonical env names from
  `requirements/10-platform-and-deployment.md` / `design/deployment-and-iac.md`
  (e.g. `dev, stg, prd`) everywhere below; never hard-code `dev/test/prod`.
- **Orchestrator deployment** - image / code-location / bundle; how schedules and
  sensors are registered; how the reconciliation gate is expressed (blocking
  check / short-circuit task) from `pipeline-blueprint.md`. Name the orchestrator
  package `<project>_dagster/` (or `dags/` for Airflow, `flows/` for Prefect) -
  **never a bare `dagster/`**, which shadows the `dagster` library on import.
- **IaC module set & apply order** - from `deployment-and-iac.md`; state backend
  bootstrap; dir-per-env vs workspaces.
- **CI/CD workflows** - PR checks, merge-to-main deploy, promotion with manual
  gates; OIDC vs stored secrets; slim CI selector.
- **Git workflow** - branching, required checks, pre-commit, CODEOWNERS,
  versioning.
- **Config layering** - defaults -> per-env -> IaC outputs -> secret refs.

Anything the design does not pin down becomes a `TODO` with a pointer, not a
guess.

## Step 2 - Write the deliverables

Write to `<WS>/pipeline/`, from the matching harness templates:

| File | What it contains |
|------|------------------|
| `repo-layout.md` | The repo tree, ownership, generated-vs-authored, how `build/repo/` becomes the real repo. |
| `orchestration-wiring.md` | Per pipeline: design task -> component call -> orchestrator unit; triggers; retry policy; the reconciliation gate wiring; the backfill entrypoint; the skeleton files to scaffold. |
| `iac-plan.md` | Module tree, per-module resource inventory (each traced to a design ref), state backend bootstrap, apply order, per-env variables, what IaC does not manage. |
| `cicd-plan.md` | The `pr` / `main` / `promote` workflows: jobs, steps, gates, promotion rules, secrets/auth, branch protection. |
| `git-workflow.md` | Branch model, PR rules, pre-commit hooks, versioning, CODEOWNERS, first-push steps. |
| `environments-and-config.md` | Env matrix, config layering, promotion, drift detection, the config-keys inventory. |
| `README.md` | Index + one-line status + date. |

Then **scaffold skeletons** inside `<WS>/build/repo/` (extending the Phase 3
tree):

- `infra/modules/<name>/{main.tf,variables.tf,outputs.tf}` and
  `infra/envs/<env>/{backend.tf,main.tf,<env>.tfvars}` - **one dir per env named
  in `requirements/10`** (not a hard-coded `dev/test/prod`); resource blocks
  named and wired, variables declared, **values as `var.` refs or `TODO`**. Keep
  the `<env>.tfvars` region consistent with `requirements/02` (do not reuse the
  DR region as the primary).
- The orchestrator project (`<project>_dagster/` / `dags/` / `flows/` - never a
  bare `dagster/`): one pipeline file per `pipeline-blueprint.md` pipeline with
  tasks named, dependency edges wired, retry config set, the gate as a
  short-circuit / **blocking check bound to a concrete asset key** (not a
  multi-asset); `resources`/`config` (use the framework's real resource types,
  e.g. `DbtCliResource`), `schedules`, `sensors`, `backfill` stubs.
- `.github/workflows/{pr,main,promote}.yml` (or the chosen CI equivalent) - jobs,
  `needs:`, environments, secret references; commands real, account values `TODO`.
  Keep env-var names (e.g. `DATABRICKS_HOST`) identical between the workflows,
  the orchestrator resources and `dbt/profiles/profiles.yml`.
- `.pre-commit-config.yaml`, `CODEOWNERS`, and one `config/<env>.yml` per
  environment (+ `config/defaults.yml`) skeletons. Add `dbt/profiles/profiles.yml`
  targets for every env the promote workflow builds.

Skeletons only. No real account ids, ARNs, hostnames, tokens, or business logic.

You may run the `pipeline-assembler` subagent for the bulk work: pass it `<WS>`.
Review before closing out.

## Step 2.9 - Self-check (do not skip)

From `<WS>/build/repo/`: `python -m compileall -q <orchestrator pkg>`;
`yaml.safe_load` every workflow + `config/*.yml` + `deployment.yaml`;
`terraform fmt -check -recursive infra` and `terraform validate` per env module
where the toolchain is present (else say it was not run). Confirm every
`pipeline/` deliverable exists and is non-empty. Fix before Step 3.

## Step 3 - Review with the user

Present: the repo tree, the orchestration wiring for one pipeline end to end, the
IaC module list + apply order, and the CI/CD flow. Ask for corrections. Revise.
Then **run `/validate-config`** and resolve each GAP it reports, or record the
GAP explicitly in `progress.json` for Phase 5 to pick up - do not close Phase 4
with unaddressed GAPs.

## Step 4 - Close out

Update `<WS>/progress.json`: `phases.4_pipeline_and_git.status`, `deliverables`,
`updated`, a `history` entry, `active_phase` -> `5_full_testing_and_hardening`.
Tell the user Phase 5 (`/harden-pipeline`) is next, and that pushing the repo /
running `terraform apply` is a human step outside this harness.

## Guardrails

- Plan and scaffold only - never run `terraform`, deploy, or `git push`.
- Every module / job / task traces to a design or build element.
- No secret values, account ids, ARNs, or hostnames - references and `TODO`s.
- Never write outside `<WS>/` except to read harness templates.
