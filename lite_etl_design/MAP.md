# MAP - the whole harness on one page

Start here. This page groups every file, shows the real flow, separates the main
path from the helpers, and answers "where does my project live".

> **Want to see a finished example?** Two full worked demos, each with a
> `README.md` documenting exactly which commands were run:
> [`projects/sample_project/`](projects/sample_project/README.md) (banking client
> "Meridian Trust", Snowflake + Airflow) and
> [`projects/sample_project_2/`](projects/sample_project_2/README.md) (retailer
> "Northwind Commerce", Databricks + dbt + Terraform + Dagster - exercises the
> platform / transformation-framework / deployment area). Both were taken through
> the design steps (1-2); the build steps (3-5) run the same way.

---

## 1. Two things: the harness vs a project

| | **The harness** (this folder) | **A project** (a workspace folder) |
|---|---|---|
| What it is | The reusable tool: commands, skills, agents, templates, question bank, the session hook. | One ETL data-harness design effort and its deliverables. |
| Changes per project? | No. Install once, use for many projects. | Yes. One folder per project. |
| Lives where | the `lite_etl_design/` folder (wherever you cloned it) | `projects/<name>/` **or any other folder on disk** (see [section 6](#6-where-can-a-project-live)). |
| Tracked in git | Yes (the harness repo). | `projects/*` yes; an external folder is yours to version separately. |
| Created by | already here | [`/etl-new-project <name>`](.claude/commands/etl-new-project.md) |

The harness never writes into itself during a design. It reads its templates and
writes into the **active project workspace**, whose path is stored in one line in
[`state/active-workspace`](state/README.md).

---

## 2. The main flow

```
        ┌─────────────────────┐
        │  /etl-new-project   │   creates <workspace>/  (intake, requirements, design, notes,
        │       <name>        │   project.json, progress.json) and marks it active
        └──────────┬──────────┘
                   │
   (optional) drop existing specs, mapping sheets, data dictionaries
   into  <workspace>/intake/
                   │
                   ▼
        ┌─────────────────────┐   skill: gather-etl-requirements   (interactive, main thread)
        │ /gather-requirements│   reads: intake/, question-bank.md, requirements/templates/
        │                     │   interviews you across 11 areas, asks about gaps
        └──────────┬──────────┘   writes: <workspace>/requirements/00..10 + README + 99-open-questions
                   │              updates: <workspace>/progress.json  (phase 1 -> complete)
                   │
                   │   (re-run /finalize-requirements anytime to fold in answers to open questions)
                   ▼
        ┌─────────────────────┐   skill: design-etl-architecture
        │ /design-architecture│   reads: <workspace>/requirements/*
        │                     │   writes: <workspace>/design/  (overview, 3 mermaid diagrams,
        │                     │           components, transformation-design (dbt),
        │                     │           deployment-and-iac (Terraform + CI/CD),
        └──────────┬──────────┘           pipeline blueprint, decisions, traceability)
                   │              updates: <workspace>/progress.json  (phase 2 -> complete)
                   ▼
        ┌─────────────────────┐   skill: build-etl-components
        │ /build-components    │   reads: <workspace>/design/*
        │                     │   writes: <workspace>/build/  (build-plan, per-component buildsheets,
        │                     │           dbt-project-scaffold, fixtures-catalog, local-dev)
        └──────────┬──────────┘   scaffolds: <workspace>/build/repo/  (dbt stubs, extractor stubs, unit tests)
                   ▼
        ┌─────────────────────┐   skill: assemble-etl-pipeline   (helper: /validate-config)
        │ /assemble-pipeline   │   reads: <workspace>/design/* + build/*
        │                     │   writes: <workspace>/pipeline/  (repo-layout, orchestration-wiring,
        │                     │           iac-plan, cicd-plan, git-workflow, environments-and-config)
        └──────────┬──────────┘   scaffolds: infra/ + orchestrator + .github/workflows/ in build/repo/
                   ▼
        ┌─────────────────────┐   skill: harden-etl-pipeline
        │ /harden-pipeline     │   reads: <workspace>/requirements + design + build + pipeline
        │                     │   writes: <workspace>/hardening/  (test-strategy, dq-behaviour-matrix,
        │                     │           reconciliation-fixtures, integration-e2e-plan, ci-gates,
        └──────────┬──────────┘           observability-wiring, security-review, runbook, go-live-checklist)
                   ▼
        hardening/go-live-checklist.md is the handoff. Running terraform / dbt /
        deploys / tests / drills are human steps - the harness executes nothing.
```

At any point: [`/etl-design-status`](.claude/commands/etl-design-status.md) tells
you where you are and the one next command. The **SessionStart hook** prints the
same summary automatically when you open Claude Code here.

---

## 3. Commands - main path vs helpers

### Main path (run in this order, once per project)

| Command | File | Runs | Reads | Writes |
|---------|------|------|-------|--------|
| `/etl-new-project <name\|path>` | [etl-new-project.md](.claude/commands/etl-new-project.md) | inline | `state/progress.template.json` | new `<workspace>/` + `state/active-workspace` |
| `/gather-requirements [note]` | [gather-requirements.md](.claude/commands/gather-requirements.md) | skill [`gather-etl-requirements`](.claude/skills/gather-etl-requirements/SKILL.md) | `<ws>/intake/`, [`question-bank.md`](requirements/question-bank.md), [`requirements/templates/`](requirements/templates/) | `<ws>/requirements/*` , `<ws>/progress.json` |
| `/design-architecture [focus]` | [design-architecture.md](.claude/commands/design-architecture.md) | skill [`design-etl-architecture`](.claude/skills/design-etl-architecture/SKILL.md) | `<ws>/requirements/*`, [`design/templates/`](design/templates/) | `<ws>/design/*` , `<ws>/progress.json` |
| `/build-components [focus]` | [build-components.md](.claude/commands/build-components.md) | skill [`build-etl-components`](.claude/skills/build-etl-components/SKILL.md) | `<ws>/design/*`, [`build/templates/`](build/templates/) | `<ws>/build/*` + `<ws>/build/repo/` , `<ws>/progress.json` |
| `/assemble-pipeline [focus]` | [assemble-pipeline.md](.claude/commands/assemble-pipeline.md) | skill [`assemble-etl-pipeline`](.claude/skills/assemble-etl-pipeline/SKILL.md) | `<ws>/design/* + build/*`, [`pipeline/templates/`](pipeline/templates/) | `<ws>/pipeline/*` + skeletons in `<ws>/build/repo/` , `<ws>/progress.json` |
| `/harden-pipeline [focus]` | [harden-pipeline.md](.claude/commands/harden-pipeline.md) | skill [`harden-etl-pipeline`](.claude/skills/harden-etl-pipeline/SKILL.md) | `<ws>/requirements + design + build + pipeline`, [`hardening/templates/`](hardening/templates/) | `<ws>/hardening/*` , `<ws>/progress.json` |

### Auxiliary helpers (run any time, any number of times)

| Command | File | What it does |
|---------|------|--------------|
| `/etl-design-status` | [etl-design-status.md](.claude/commands/etl-design-status.md) | Short status block: active project, phase, what's done, what's missing, next command. Read-only. |
| `/finalize-requirements` | [finalize-requirements.md](.claude/commands/finalize-requirements.md) | Re-run Phase 1 **Step 2 onward** only - rewrite the requirement files from notes / updated open-question answers, without the full interview. |
| `/validate-config` | [validate-config.md](.claude/commands/validate-config.md) | Read-only gap report on the Phase 4 wiring (orchestration / IaC / CI-CD plans vs the design, the build, and the scaffold). |
| `/etl-design-help` | [etl-design-help.md](.claude/commands/etl-design-help.md) | Briefing on the harness, phases, and your current next step (reads this MAP + README). |

`/etl-new-project` is also a helper when pointed at an **existing** workspace: it
just switches the active project, scaffolding nothing.

---

## 4. Every file, grouped

### A. Claude Code surface - [`.claude/`](.claude/)

| File | Type | Role |
|------|------|------|
| [`.claude/settings.json`](.claude/settings.json) | config | registers the SessionStart hook |
| [`.claude/hooks/session_context.py`](.claude/hooks/session_context.py) | hook | prints active project + phase status at session start; never fails the session |
| [`.claude/commands/`](.claude/commands/) ×10 | slash commands | thin entry points - see [section 3](#3-commands---main-path-vs-helpers) |
| [`.claude/skills/gather-etl-requirements/SKILL.md`](.claude/skills/gather-etl-requirements/SKILL.md) | skill | Phase 1 - interactive requirements interview |
| [`.claude/skills/design-etl-architecture/SKILL.md`](.claude/skills/design-etl-architecture/SKILL.md) | skill | Phase 2 - architecture + diagrams + dbt/IaC design |
| [`.claude/skills/build-etl-components/SKILL.md`](.claude/skills/build-etl-components/SKILL.md) | skill | Phase 3 - build plan + buildsheets + repo scaffold |
| [`.claude/skills/assemble-etl-pipeline/SKILL.md`](.claude/skills/assemble-etl-pipeline/SKILL.md) | skill | Phase 4 - orchestration wiring + IaC plan + CI/CD plan + skeletons |
| [`.claude/skills/harden-etl-pipeline/SKILL.md`](.claude/skills/harden-etl-pipeline/SKILL.md) | skill | Phase 5 - tests, CI gates, observability, security review, runbook, go-live |
| [`.claude/agents/requirements-synthesizer.md`](.claude/agents/requirements-synthesizer.md) | subagent | optional - drafts Phase 1 files (non-interactive) |
| [`.claude/agents/solution-architect.md`](.claude/agents/solution-architect.md) | subagent | optional - drafts the Phase 2 design set |
| [`.claude/agents/component-builder.md`](.claude/agents/component-builder.md) | subagent | optional - drafts Phase 3 buildsheets + scaffolds `build/repo/` |
| [`.claude/agents/pipeline-assembler.md`](.claude/agents/pipeline-assembler.md) | subagent | optional - drafts the Phase 4 pipeline set + skeletons |
| [`.claude/agents/hardening-planner.md`](.claude/agents/hardening-planner.md) | subagent | optional - drafts the Phase 5 hardening set |

### B. Shared Phase 1 inputs - [`requirements/`](requirements/) (harness, not per-project)

| File | Role |
|------|------|
| [`requirements/README.md`](requirements/README.md) | explains this folder |
| [`requirements/question-bank.md`](requirements/question-bank.md) | the coverage checklist the interview follows (11 areas) |
| [`requirements/templates/00-project-brief.md`](requirements/templates/00-project-brief.md) | business goal, stakeholders, success criteria, scope |
| [`requirements/templates/01-source-systems.md`](requirements/templates/01-source-systems.md) | per source: type, reach, auth, objects, mode, volume, quirks |
| [`requirements/templates/02-targets-and-loading.md`](requirements/templates/02-targets-and-loading.md) | target platform, landing zone, load patterns, idempotency |
| [`requirements/templates/03-transformations.md`](requirements/templates/03-transformations.md) | cleansing, standardisation, dedupe, historisation, keys, ETL vs ELT |
| [`requirements/templates/04-data-quality.md`](requirements/templates/04-data-quality.md) | DQ dimensions, concrete rules, thresholds, reporting |
| [`requirements/templates/05-reconciliation.md`](requirements/templates/05-reconciliation.md) | row counts, control totals, balancing, tolerances, gate |
| [`requirements/templates/06-lineage-and-governance.md`](requirements/templates/06-lineage-and-governance.md) | lineage granularity, catalog, ownership, audit |
| [`requirements/templates/07-scheduling-and-orchestration.md`](requirements/templates/07-scheduling-and-orchestration.md) | cadence, SLA, dependencies, orchestrator, retries, alerting |
| [`requirements/templates/08-security-and-compliance.md`](requirements/templates/08-security-and-compliance.md) | PII/PHI, masking, encryption, secrets, access, regulation |
| [`requirements/templates/09-non-functional.md`](requirements/templates/09-non-functional.md) | scale, latency, cost, environments, CI/CD, observability, DR |
| [`requirements/templates/10-platform-and-deployment.md`](requirements/templates/10-platform-and-deployment.md) | target engine(s) & portability, dbt project (layers, materialisations, snapshots, tests, packages), Terraform / IaC scope & state, CI/CD promotion & rollback, env topology |
| [`requirements/templates/99-open-questions.md`](requirements/templates/99-open-questions.md) | gap / assumption / owner tracker |

### C. Shared Phase 2 templates - [`design/`](design/) (harness, not per-project)

| File | Role |
|------|------|
| [`design/README.md`](design/README.md) | explains this folder |
| [`design/templates/architecture-overview.md`](design/templates/architecture-overview.md) | approach, component inventory, cross-cutting concerns |
| [`design/templates/architecture-diagram.md`](design/templates/architecture-diagram.md) | Mermaid flowchart skeleton of the whole harness |
| [`design/templates/data-flow-diagram.md`](design/templates/data-flow-diagram.md) | Mermaid per-source zone flow + checkpoints |
| [`design/templates/data-entity-diagram.md`](design/templates/data-entity-diagram.md) | Mermaid ER skeleton (target + staging) |
| [`design/templates/component-design.md`](design/templates/component-design.md) | per-component responsibility / interfaces / failure modes |
| [`design/templates/transformation-design.md`](design/templates/transformation-design.md) | dbt project blueprint: layers, sources & freshness, materialisation & incremental strategy, SCD2 snapshots, DQ-as-tests, packages, docs & exposures, `dbt build` run interface |
| [`design/templates/deployment-and-iac.md`](design/templates/deployment-and-iac.md) | Terraform module layout, IaC scope, state backend, env isolation, the CI/CD `plan -> apply -> dbt build -> promote` pipeline (Mermaid), rollback, drift, env topology |
| [`design/templates/pipeline-blueprint.md`](design/templates/pipeline-blueprint.md) | task DAG, retry/backfill, reconciliation gate |
| [`design/templates/design-decisions.md`](design/templates/design-decisions.md) | ADR record format + typical decision list |
| [`design/templates/traceability-matrix.md`](design/templates/traceability-matrix.md) | requirement -> design element coverage table |

### D. Shared Phase 3 templates - [`build/`](build/) (harness, not per-project)

| File | Role |
|------|------|
| [`build/README.md`](build/README.md) | explains this folder |
| [`build/templates/build-plan.md`](build/templates/build-plan.md) | component build order, "component complete" definition, local-run summary, CI hook |
| [`build/templates/component-buildsheet.md`](build/templates/component-buildsheet.md) | per component: design refs, files, interface, config keys, unit-test table, fixtures, done checklist |
| [`build/templates/dbt-project-scaffold.md`](build/templates/dbt-project-scaffold.md) | dbt tree to create + model/test/snapshot/seed -> design-section map + macros + run targets |
| [`build/templates/fixtures-catalog.md`](build/templates/fixtures-catalog.md) | per source: sample / empty / late / duplicate / drift / bad-rows / partial fixtures + golden outputs + recon fixtures |
| [`build/templates/local-dev.md`](build/templates/local-dev.md) | prereqs, task-runner targets, how each source is faked locally, the dev loop |

### E. Shared Phase 4 templates - [`pipeline/`](pipeline/) (harness, not per-project)

| File | Role |
|------|------|
| [`pipeline/README.md`](pipeline/README.md) | explains this folder |
| [`pipeline/templates/repo-layout.md`](pipeline/templates/repo-layout.md) | the repo tree, ownership, generated-vs-authored, how `build/repo/` becomes the real repo |
| [`pipeline/templates/orchestration-wiring.md`](pipeline/templates/orchestration-wiring.md) | design task -> component -> orchestrator unit; triggers; retries; the reconciliation gate; backfill entrypoint |
| [`pipeline/templates/iac-plan.md`](pipeline/templates/iac-plan.md) | Terraform module tree, per-module resource inventory, state backend bootstrap, apply order, per-env vars |
| [`pipeline/templates/cicd-plan.md`](pipeline/templates/cicd-plan.md) | `pr` / `main` / `promote` workflows, gates, promotion rules, secrets/OIDC, branch protection |
| [`pipeline/templates/git-workflow.md`](pipeline/templates/git-workflow.md) | branch model, PR rules, pre-commit hooks, versioning, CODEOWNERS, first-push |
| [`pipeline/templates/environments-and-config.md`](pipeline/templates/environments-and-config.md) | env matrix, config layering, promotion, drift detection, config-keys inventory |

### F. Shared Phase 5 templates - [`hardening/`](hardening/) (harness, not per-project)

| File | Role |
|------|------|
| [`hardening/README.md`](hardening/README.md) | explains this folder |
| [`hardening/templates/test-strategy.md`](hardening/templates/test-strategy.md) | the test pyramid, coverage targets, test environments, what gates merge vs deploy vs promote |
| [`hardening/templates/dq-behaviour-matrix.md`](hardening/templates/dq-behaviour-matrix.md) | every DQ rule x input scenario -> expected routing (pass / warn / quarantine / fail) |
| [`hardening/templates/reconciliation-fixtures.md`](hardening/templates/reconciliation-fixtures.md) | per recon check: PASS / FAIL / boundary fixture + expected gate action |
| [`hardening/templates/integration-e2e-plan.md`](hardening/templates/integration-e2e-plan.md) | integration + contract + end-to-end scenarios, stubbed-vs-real, runtime budget |
| [`hardening/templates/ci-gates.md`](hardening/templates/ci-gates.md) | merge / deploy / promote gates, branch protection, nightly suite, security + IaC scans |
| [`hardening/templates/observability-wiring.md`](hardening/templates/observability-wiring.md) | metrics / logs / dashboards / alert rules mapped to 07/09, SLOs, healthy definition |
| [`hardening/templates/security-review.md`](hardening/templates/security-review.md) | the 08 checklist walked against the build, findings table, sign-off |
| [`hardening/templates/runbook.md`](hardening/templates/runbook.md) | normal day, common failures + fixes, backfill procedure, rollback procedure, escalation |
| [`hardening/templates/go-live-checklist.md`](hardening/templates/go-live-checklist.md) | readiness items, drills (backfill / rollback / failure / DR), cutover steps, go-live rollback plan, sign-offs |

### G. Harness state - [`state/`](state/)

| File | Role |
|------|------|
| [`state/README.md`](state/README.md) | explains this folder |
| `state/active-workspace` | one line: path of the current project (git-ignored, machine-local) |
| [`state/progress.template.json`](state/progress.template.json) | starting `progress.json` copied into each new workspace |

### H. Docs

| File | Role |
|------|------|
| [`README.md`](README.md) | full narrative: quick start, folder map, how skills/tools/subagents/hooks work |
| [`MAP.md`](MAP.md) | this page |
| [`docs/process-overview.md`](docs/process-overview.md) | all five steps and what each produces |

### I. A project workspace (created by `/etl-new-project`) - *not* in the harness

```
<workspace>/
├── project.json          name, created date, harness path/version
├── progress.json          per-project phase tracker
├── README.md              points back to the harness
├── intake/                YOU drop existing source docs here
├── requirements/          Phase 1 deliverables: 00..10 + README + 99-open-questions
├── design/                Phase 2 deliverables: overview + diagrams + components +
│                          transformation-design + deployment-and-iac + ...
├── build/                 Phase 3: build-plan + buildsheets + fixtures + local-dev
│   └── repo/              scaffolded starter repo (dbt stubs, extractor stubs, tests,
│                          then infra/ + orchestrator + CI skeletons from Phase 4)
├── pipeline/              Phase 4: repo-layout + orchestration + IaC + CI/CD + git + envs
├── hardening/             Phase 5: test-strategy + DQ matrix + recon fixtures + CI gates
│                          + observability + security-review + runbook + go-live-checklist
└── notes/                 optional interview transcripts / scratch
```

---

## 5. Skill vs tool vs subagent vs command vs hook (in this harness)

| Building block | Where | Triggered by | Can talk to you? | Used here for |
|---------------|-------|--------------|------------------|---------------|
| **Slash command** | `.claude/commands/*.md` | you type `/name` | n/a (it's just a prompt) | thin entry points that invoke a skill and pass your focus note |
| **Skill** | `.claude/skills/<name>/SKILL.md` | a command, or you describing the task | yes (runs on the main thread) | one procedure per phase (1-5) - what to read, ask, write, scaffold |
| **Tool** | built in | a skill, while running | `AskUserQuestion` does | `Read`/`Write`/`Edit`/`Glob`/`Grep`/`Bash` + `AskUserQuestion` for the interview's multiple-choice parts. No custom tools, no MCP server - the job is reading answers, writing Markdown, and scaffolding skeleton files (Phases 3-4). It runs nothing (`terraform`, `dbt`, deploys, `git push`, tests are human steps). |
| **Subagent** | `.claude/agents/*.md` | a skill choosing to delegate | **no** - runs autonomously, returns a summary | optional heavy drafting only (`requirements-synthesizer`, `solution-architect`, `component-builder`, `pipeline-assembler`, `hardening-planner`); never the interview |
| **Hook** | `.claude/settings.json` -> `hooks/session_context.py` | automatically, at session start | no (prints text) | the one-line status banner |

Rule of thumb: **commands** are the door, **skills** are the method, **tools**
are the hands, **subagents** are extra hands for bulk writing, the **hook** is
the sign on the wall telling you where you left off.

---

## 6. Where can a project live?

**Yes - a project can be a subfolder or a completely separate folder.** The
harness is a reusable tool; each project is a workspace you point it at.

| You run | Workspace created at | Use when |
|---------|----------------------|----------|
| `/etl-new-project sales-dwh` | `projects/sales-dwh/` (inside the harness) | quick start; you're fine keeping designs alongside the harness and in its git repo |
| `/etl-new-project ../design-work/sales-dwh` | resolved relative to the harness | you want it next to the harness but outside its repo |
| `/etl-new-project D:\clients\acme\etl-design` | that exact absolute path | the project belongs in its own repo / a client folder / a shared drive |

Only one project is **active** at a time - the one named in
`state/active-workspace`. To switch, run `/etl-new-project` again pointing at an
existing workspace (it detects `project.json` and just re-activates it, changing
nothing). `/etl-design-status` lists workspaces under `projects/`.

Each workspace is self-contained (`project.json` records which harness made it),
so you can move it, zip it, or commit it to a different repo freely.

---

## 7. "I want to..." quick reference

| Goal | Do |
|------|-----|
| Start a new ETL design | `/etl-new-project <name>` then `/gather-requirements` |
| Work on a design in its own repo folder | `/etl-new-project C:\path\to\folder` |
| Switch back to an earlier project | `/etl-new-project <its path or projects/<name>>` |
| See where I am | `/etl-design-status` (or just start a session - the hook prints it) |
| Feed in a spec I already have | drop it in `<workspace>/intake/` before `/gather-requirements` |
| I answered some open questions | edit `<workspace>/requirements/99-open-questions.md`, then `/finalize-requirements` |
| Move on to architecture | `/design-architecture` |
| Scaffold the components + dbt project | `/build-components` (after Phase 2) |
| Wire the orchestrator + IaC + CI/CD | `/assemble-pipeline` (after Phase 3), then `/validate-config` |
| Add tests, gates, runbook, go-live | `/harden-pipeline` (after Phase 4) |
| Tweak a diagram visually | copy the ```mermaid block into mermaid.live |
| Change how a phase works | edit the `SKILL.md`, not the command |
| Add a step 6 | ask - same pattern: skill + command + optional subagent + a `<step>/templates/` folder + a phase in `progress.template.json` |
