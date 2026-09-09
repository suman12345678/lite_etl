# The ETL data-harness design process

A step-by-step method for designing and building an ETL data harness. Each step
produces reviewable artifacts that feed the next. **Only steps 1 and 2 are built
today**; the rest are the roadmap and will be added as separate harness pieces.

Each design effort is a **project workspace** (`projects/<name>/` or any folder
on disk) created with `/etl-new-project`. The harness holds the templates and
commands; the workspace holds `intake/`, `requirements/`, `design/`, and
`progress.json`. See `../MAP.md`.

```
1. Requirements   2. Architecture      3. Build & test    4. Pipeline & Git   5. Full testing
   & interview   ─▶  & data modeling ─▶   components    ─▶   & CI/CD        ─▶  & hardening
   (BUILT)           (BUILT)               (planned)          (planned)          (planned)
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

## Step 3 - Build & test components  *(planned)*

Scaffold and implement the components named in Step 2 - connectors, landing
writer, the **dbt project** (staging / intermediate / marts models, snapshots,
seeds, `sources.yml`, generic + singular tests), DQ engine, reconciliation
engine, loader - each with unit tests against local fixtures (dbt runs on DuckDB
or a dev schema). Config-driven, one component at a time.

## Step 4 - Pipeline & Git  *(planned)*

Wire components into runnable pipelines for the chosen orchestrator, write the
**Terraform** modules (`envs/dev|test|prod`, state backend, providers), add
environment config, repo layout, branch strategy, and push. CI/CD pipeline:
`lint -> terraform validate -> terraform plan + dbt build on a CI schema ->
apply + dbt build on merge -> promote`. `/validate-config` + pre-commit hooks.

## Step 5 - Full testing & hardening  *(planned)*

Integration and end-to-end tests, contract tests, data-quality behaviour
matrices, reconciliation fixtures, `dbt build` + `terraform plan` CI gates,
drift detection, observability wiring, security review, runbook, backfill
drills, a prod rollback drill.

## State

`<workspace>/progress.json` tracks per-phase status and the list of delivered
files for that project. `/etl-design-status` reads it and tells you the next
command. `state/active-workspace` (harness root) records which project is active.
The SessionStart hook prints a one-line summary each time a session starts here.

## Adding future steps

Each future step is added the same way: a skill under `.claude/skills/`, a thin
`/command` under `.claude/commands/`, an optional non-interactive subagent under
`.claude/agents/`, a shared `templates/` folder for that step's deliverables, and
a new phase entry in `state/progress.template.json` (every new workspace inherits
it). Ask for "step 3" when ready.
