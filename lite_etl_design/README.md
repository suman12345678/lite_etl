# lite-etl-design

A **design harness** for building an ETL data harness, one step at a time.

An ETL data harness has to account for a lot - data quality, data lineage, the
pipeline itself, reconciliation, extraction from many source types (SQL, CSV,
BigQuery, APIs), transformation logic, loading, scheduling, security, and how the
whole thing is provisioned and shipped. Designing all of that in one pass
produces something vague. This harness breaks the work into ordered steps, each
producing reviewable artifacts that feed the next.

**Assumed stack (state it, override it):** a **warehouse-agnostic** target
(Snowflake / Databricks / BigQuery / Redshift / ...), **dbt** for
transformations, **Terraform** for infrastructure and deployment, driven by a
CI/CD pipeline. The interview in step 1 confirms or changes each of these; the
design in step 2 produces a dbt project blueprint and a Terraform + CI/CD
deployment design alongside the architecture.

```
1. Requirements   2. Architecture      3. Build & test    4. Pipeline & Git   5. Full testing
   & interview   ─▶  & data modeling ─▶   components    ─▶   & CI/CD        ─▶  & hardening
   BUILT             BUILT                 planned            planned            planned
```

**This folder currently implements steps 1 and 2.** Steps 3-5 are described in
[`docs/process-overview.md`](docs/process-overview.md) and will be added later.

> **New here? Read [`MAP.md`](MAP.md)** - every file grouped and linked, the real
> flow, the helper commands, and where your project lives, all on one page.
>
> **Want a finished example?** Two full demos, each a fictional client taken
> through steps 1 and 2 with a README that shows which commands were run and what
> each produced:
> - [`projects/sample_project/`](projects/sample_project/README.md) - a banking
>   client on **Snowflake + Airflow**.
> - [`projects/sample_project_2/`](projects/sample_project_2/README.md) - a
>   retailer on **Databricks + dbt + Terraform + Dagster**, exercising the
>   platform / transformation-framework / deployment area.

---

## The harness vs a project

- **The harness** = this folder. The reusable tool: commands, skills, agents,
  templates, the session hook. You do not edit it per project.
- **A project** = a *workspace* folder the harness writes into. One per ETL
  design effort. It can be a **subfolder** (`projects/<name>/`) or **any other
  folder on disk** (e.g. `D:\clients\acme\etl-design`). See
  [MAP.md section 6](MAP.md#6-where-can-a-project-live).

Only one project is active at a time; its path is stored in
[`state/active-workspace`](state/README.md).

---

## Quick start

```
cd <path to>/lite_etl_design
claude
```

Then:

| Step | Run | Result |
|------|-----|--------|
| Create a project | `/etl-new-project sales-dwh` | scaffolds `projects/sales-dwh/`, marks it active |
| (optional) add material you have | drop files in `projects/sales-dwh/intake/` | the interview reads them first |
| **Step 1** - gather requirements | `/gather-requirements` | interactive interview -> `projects/sales-dwh/requirements/*.md` |
| **Step 2** - architecture & diagrams | `/design-architecture` | -> `projects/sales-dwh/design/*.md` (incl. Mermaid diagrams) |
| Any time - where am I? | `/etl-design-status` | short status + the one next command |
| Any time - explain the harness | `/etl-design-help` | briefing |
| Redo just the requirement files | `/finalize-requirements` | rewrites them without the full interview |

To work on a project in its own repo folder instead:
`/etl-new-project D:\path\to\folder`. To switch back to an earlier project, run
`/etl-new-project` again with its path.

---

## Step 1 - Requirements gathering

`/gather-requirements` runs the [`gather-etl-requirements`](.claude/skills/gather-etl-requirements/SKILL.md)
skill. It:

1. Resolves the active workspace, reads anything in its `intake/`, and the
   checklist in [`requirements/question-bank.md`](requirements/question-bank.md).
2. Walks through eleven areas - **project brief, source systems, targets &
   loading, transformations, data quality, reconciliation, lineage & governance,
   scheduling & orchestration, security & compliance, non-functional, and
   platform / transformation framework / deployment** (target engine &
   portability, dbt project shape, Terraform / IaC, CI/CD promotion) - asking
   only what is still unknown, in small batches, using multiple-choice prompts
   for decisions.
3. Lets you answer "use your judgement" for anything you don't care about - the
   assumption is then written down explicitly.
4. Writes one file per area to `<workspace>/requirements/`, plus a `README.md`
   index and `99-open-questions.md` (every gap + assumption, numbered, with an
   owner).
5. Updates `<workspace>/progress.json`.

Review the files, edit anything directly, fill in `99-open-questions.md` as you
get answers (re-run `/finalize-requirements` to fold them in).

## Step 2 - Architecture & data modeling

`/design-architecture` runs the [`design-etl-architecture`](.claude/skills/design-etl-architecture/SKILL.md)
skill. It:

1. Confirms Step 1 is done for the active workspace (else sends you back).
2. Settles the load-bearing choices - ETL vs ELT, batch vs streaming per source,
   zone model, orchestration, storage/formats, idempotency, transformation
   framework & warehouse portability (dbt adapter, layers, materialisations),
   infrastructure & deployment (IaC tool, CI/CD promotion) - each traced to a
   specific requirement.
3. Writes to `<workspace>/design/`:
   `architecture-overview.md`, `architecture-diagram.md` (Mermaid flowchart),
   `data-flow-diagram.md` (Mermaid per-source zone flow), `data-entity-diagram.md`
   (Mermaid ER), `component-design.md`, `transformation-design.md` (the dbt
   project blueprint), `deployment-and-iac.md` (Terraform module layout + the
   CI/CD `plan -> apply -> dbt build -> promote` pipeline), `pipeline-blueprint.md`
   (task DAG + the reconciliation gate), `design-decisions.md` (ADR-style),
   `traceability-matrix.md` (every requirement -> design element), `README.md`.
4. Walks you through the approach, diagrams, and key decisions; revises on
   feedback. Updates `<workspace>/progress.json`.

Diagrams are Mermaid - they render in GitHub and Claude artifacts; paste any
block into `mermaid.live` to tweak it visually.

---

## Folder map

```
lite_etl_design/                 THE HARNESS (reusable)
├── README.md                    this file
├── MAP.md                       everything grouped + linked, on one page  ◀── read this
├── .gitignore
│
├── .claude/
│   ├── settings.json            registers the SessionStart hook
│   ├── commands/                6 thin /slash-command entry points
│   │   etl-new-project · gather-requirements · finalize-requirements
│   │   design-architecture · etl-design-status · etl-design-help
│   ├── skills/                  the actual procedures
│   │   gather-etl-requirements/SKILL.md      (Step 1, interactive)
│   │   design-etl-architecture/SKILL.md      (Step 2)
│   ├── agents/                  optional non-interactive helpers (subagents)
│   │   requirements-synthesizer.md · solution-architect.md
│   └── hooks/session_context.py one-line status at session start
│
├── requirements/               SHARED Phase 1 inputs
│   ├── question-bank.md         the interview coverage checklist (11 areas)
│   └── templates/               00..10 + 99 blank per-area templates
│                                (10 = platform / dbt / Terraform / CI-CD)
│
├── design/                     SHARED Phase 2 templates
│   └── templates/              architecture / diagrams / components / transformation
│                                (dbt) / deployment-and-iac (Terraform) / ADRs / traceability
│
├── docs/process-overview.md    all five steps; what each produces
│
├── state/
│   ├── active-workspace         one line: path of the current project (git-ignored)
│   └── progress.template.json   copied into each new workspace
│
└── projects/                   PROJECT WORKSPACES created by /etl-new-project
    └── <name>/
        ├── project.json  progress.json  README.md
        ├── intake/             ◀── you drop existing docs here
        ├── requirements/       ◀── Step 1 deliverables land here
        ├── design/             ◀── Step 2 deliverables land here
        └── notes/
```

(A project created outside the harness has the same `<name>/…` shape, just at
your chosen path.)

---

## How the harness works - skills, tools, subagents, commands, hooks

Claude Code building blocks, and how this harness uses each. (A compact table is
in [MAP.md section 5](MAP.md#5-skill-vs-tool-vs-subagent-vs-command-vs-hook-in-this-harness).)

### Slash command  (`.claude/commands/*.md`)

A Markdown file whose body is a **prompt** sent as if you typed it. Filename =
command name. YAML front-matter sets the `description` and `argument-hint`;
`$ARGUMENTS` in the body is replaced by whatever you type after the command.

Commands here are deliberately **thin** - a few lines that say "resolve the
workspace, invoke skill X, here is my focus note". The real logic is in the
skill, so the behaviour is the same whether you use the command or just ask.

- `/etl-new-project <name|path>` - scaffold / switch the active project workspace
- `/gather-requirements [note]` - run the Step 1 skill (interactive interview)
- `/finalize-requirements` - Step 1 skill from Step 2 onward (write files only)
- `/design-architecture [focus]` - run the Step 2 skill
- `/etl-design-status` - read progress, report the next action (read-only)
- `/etl-design-help` - explain the harness and your current next step

### Skill  (`.claude/skills/<name>/SKILL.md`)

A **procedure** Claude loads when the task matches. `name` + `description` (the
description is how Claude decides it's relevant - "let's gather ETL requirements"
pulls in `gather-etl-requirements` even without the slash command). The body is
step-by-step instructions: resolve the workspace, what to read, what order to ask
in, what files to write, how to update progress.

- `gather-etl-requirements` - Step 1. **Runs on the main thread** because it must
  talk to you.
- `design-etl-architecture` - Step 2. Reads the workspace's requirements, writes
  its design folder.

To change the process, edit the SKILL.md - not the command.

### Tools

The actions a skill takes: `Read`, `Write`, `Edit`, `Glob`, `Grep`, `Bash`, and
the interactive `AskUserQuestion` (multiple-choice prompts). This harness needs
**no custom tools and no MCP server** - the whole job is reading your answers and
writing Markdown. `AskUserQuestion` makes the Step 1 decisions feel like a form
while the open-ended parts stay a conversation.

(The sibling `dwh-extract-full` plugin *does* ship an MCP server, because it
actually runs extractions. A design harness executes nothing.)

### Subagent  (`.claude/agents/*.md`)

A **separate Claude instance** for one focused job, with its own context window,
returning only a summary. `name` + `description` + a restricted `tools` list.

Key constraint: **a subagent cannot talk to you.** So here they are only for
**non-interactive synthesis**, never the interview:

- `requirements-synthesizer` - given the interview notes + intake docs and the
  workspace path, drafts the ten requirement files + `99-open-questions.md`.
- `solution-architect` - given the workspace path, drafts the whole Step 2
  design set.

Both are **optional accelerators** - the skills work without them; they just keep
the main conversation lean for big writing jobs.

### Hook  (`.claude/settings.json` → `.claude/hooks/session_context.py`)

A **SessionStart** hook: every time you start Claude Code in this folder it runs
`session_context.py`, which prints one status block - the active project, its
phase from `progress.json`, deliverable counts, and anything waiting in `intake/`.
Pure Python standard library, and it swallows its own errors so a bad state file
can never block your session.

Hooks are the harness's *automatic* behaviour. Everything else is triggered by
you (a command) or by Claude choosing a skill.

---

## Design conventions

- **Deliverables are Markdown**, one file per concern. Harness templates are
  never edited in place - a skill copies them into the workspace and fills them.
- **Diagrams are Mermaid** in fenced ```mermaid blocks - render on GitHub and in
  artifacts, stay diffable.
- **Secrets are references, never values** - "env var `X`", "Vault path `Y`".
- **`<workspace>/progress.json` is the source of truth for progress.** Only the
  skills write it; `/etl-design-status` and the hook only read it.
- **Every design choice cites a requirement.** The traceability matrix proves
  nothing was invented and nothing dropped.

## Adding steps 3-5 later

Same pattern each time: a new skill under `.claude/skills/`, a thin `/command`, an
optional non-interactive subagent, shared `templates/`, and a new phase in
`state/progress.template.json` (which every new workspace inherits). See
[`docs/process-overview.md`](docs/process-overview.md) for what each remaining
step should produce.
