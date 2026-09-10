# The ETL data-harness design process

A step-by-step method for designing and building an ETL data harness. Each step
produces reviewable artifacts that feed the next. **All five steps are built.**
Steps 1-2 are design; steps 3-5 additionally scaffold skeleton code and plans -
but the harness still executes nothing (no `terraform apply`, no deploy, no
`git push`, no test runs - those are human steps).

Each design effort is a **project workspace** (`projects/<name>/` or any folder
on disk) created with `/etl-new-project`. The harness holds the templates and
commands; the workspace holds `intake/`, `requirements/`, `design/`, `build/`
(incl. `build/repo/`), `pipeline/`, `hardening/`, and `progress.json`. See
`../MAP.md`.

```
1. Requirements   2. Architecture      3. Build & test    4. Pipeline & Git   5. Full testing
   & interview   ─▶  & data modeling ─▶   components    ─▶   & CI/CD        ─▶  & hardening
   (BUILT)           (BUILT)               (BUILT)            (BUILT)            (BUILT)
```

## Step 1 - Requirements gathering  *(built)*

**Skill:** `gather-etl-requirements` · **Commands:** `/gather-requirements`,
`/finalize-requirements` · **Agent:** `requirements-synthesizer`

Interactive interview with you covering: project brief, source systems (SQL /
CSV / BigQuery / API / ...), targets & loading, transformation logic, data
quality, reconciliation, data lineage & governance, scheduling & orchestration,
security & compliance, non-functional needs, and platform / transformation
framework / deployment (target engine & portability - Snowflake / Databricks /
BigQuery / Redshift / ...; **dbt** project shape; **Terraform** / IaC; CI/CD
promotion). Missing answers are asked about; "use your judgement" is recorded as
an explicit assumption. The default stack - warehouse-agnostic target, dbt for
transforms, Terraform for deployment - is stated and can be overridden.

**Output:** `<workspace>/requirements/00..10.md` + `README.md` +
`99-open-questions.md`.

## Step 2 - Architecture & data modeling  *(built)*

**Skill:** `design-etl-architecture` · **Command:** `/design-architecture` ·
**Agent:** `solution-architect`

Turns the requirement files into: an architecture overview (with every choice
traced to a requirement), a Mermaid architecture diagram, per-source data-flow
diagrams, a Mermaid ER diagram of the target + staging model, component designs,
a **transformation design** (dbt project blueprint - layers, materialisations,
snapshots, tests-as-DQ, run interface), a **deployment & IaC design** (Terraform
module layout, state backend, the CI/CD `plan -> apply -> dbt build -> promote`
pipeline, rollback, env topology), a pipeline blueprint (task DAG + policies +
the reconciliation gate), an ADR-style decision log, and a requirement-to-design
traceability matrix.

**Output:** `<workspace>/design/*.md`.

## Step 3 - Build & test components  *(built)*

**Skill:** `build-etl-components` · **Command:** `/build-components` ·
**Agent:** `component-builder`

Turns Step 2 into an ordered build plan, one buildsheet per component
(interface, config keys, unit tests, fixtures, done checklist), a dbt project
scaffold doc, a fixtures catalog and a local-dev guide - and scaffolds a starter
repo under `<workspace>/build/repo/`: the dbt project with stub models /
snapshots / seeds / `sources.yml`, extractor stubs with real signatures,
unit-test stubs, tiny synthetic fixtures, a task-runner file. Stubs and `TODO`s
only; local tests run on DuckDB / mocks, no cloud.

**Output:** `<workspace>/build/*.md` + `<workspace>/build/repo/`.

## Step 4 - Pipeline & Git  *(built)*

**Skill:** `assemble-etl-pipeline` · **Commands:** `/assemble-pipeline`,
`/validate-config` · **Agent:** `pipeline-assembler`

Wires the components into orchestrator pipelines and plans the delivery:
`repo-layout.md`, `orchestration-wiring.md` (design task -> component ->
orchestrator unit, triggers, retries, the reconciliation gate, the backfill
entrypoint), `iac-plan.md` (Terraform module tree, resource inventory, state
backend bootstrap, apply order, per-env vars), `cicd-plan.md`
(`pr` / `main` / `promote` workflows, gates, OIDC), `git-workflow.md`,
`environments-and-config.md`. Scaffolds `infra/modules|envs/*`, the orchestrator
project, and `.github/workflows/*` skeletons in `build/repo/`. `/validate-config`
checks the wiring. Nothing is applied, deployed or pushed.

**Output:** `<workspace>/pipeline/*.md` + more skeletons in `build/repo/`.

## Step 5 - Full testing & hardening  *(built)*

**Skill:** `harden-etl-pipeline` · **Command:** `/harden-pipeline` ·
**Agent:** `hardening-planner`

Makes it production-ready on paper and in test: `test-strategy.md` (the pyramid
and what gates merge / deploy / promote), `dq-behaviour-matrix.md` (every `04`
rule x scenario -> routing), `reconciliation-fixtures.md` (PASS / FAIL /
boundary per `05` check), `integration-e2e-plan.md`, `ci-gates.md`,
`observability-wiring.md` (metrics, alerts, SLOs), `security-review.md` (the
`08` checklist walked, findings, sign-off), `runbook.md`, and
`go-live-checklist.md` (readiness + backfill / rollback / failure / DR drills +
cutover). Specifications only - the harness runs no tests and executes no drills.

**Output:** `<workspace>/hardening/*.md`.

## State

`<workspace>/progress.json` tracks per-phase status and the list of delivered
files for that project. `/etl-design-status` reads it and tells you the next
command. `state/active-workspace` (harness root) records which project is active.
The SessionStart hook prints a one-line summary each time a session starts here.

## The pattern (how each step is built)

Every step follows the same shape, so a sixth could be added the same way: a
skill under `.claude/skills/<name>/SKILL.md`, a thin `/command` under
`.claude/commands/`, an optional non-interactive subagent under
`.claude/agents/`, a shared `<step>/templates/` folder at the harness root for
that step's deliverables, and a phase entry in `state/progress.template.json`
(every new workspace inherits it).
