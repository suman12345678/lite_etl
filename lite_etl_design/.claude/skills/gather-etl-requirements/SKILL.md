---
name: gather-etl-requirements
description: Run Phase 1 of the ETL data-harness design process - an interactive, structured requirements interview with the user covering sources, targets, transformations, data quality, reconciliation, lineage, scheduling, security and non-functional needs - then write one requirement file per area into the active project workspace's requirements/ folder. Use when the user wants to start an ETL/data-harness design, gather requirements, or run "/gather-requirements".
---

# gather-etl-requirements  (Phase 1)

You are the **requirements interviewer** for an ETL data harness. Your job is a
conversation, not a form dump. Draw out what the user needs, notice what is
missing, ask about it, and only then write the requirement files.

This phase MUST run on the main thread (you talk to the user directly). Do not
delegate the interview to a subagent - subagents cannot ask the user questions.

## Step 0 - Resolve the workspace, then orient

1. **Find the active project workspace** (this is where output goes):
   - read `state/active-workspace` (harness root). Its one line is `<WS>`.
   - if the file is missing or `<WS>/project.json` does not exist, tell the user
     to run `/etl-new-project <name>` first, and stop.
   All deliverable paths below are relative to `<WS>`. Templates, the question
   bank, and this skill are read from the **harness** root.
2. Read `<WS>/progress.json`. Note the active phase and anything already done.
3. Read every file in `<WS>/intake/` (skip `.gitkeep`). These are docs the user
   dropped in - existing specs, mapping sheets, data dictionaries, emails.
   Extract every fact you can so you do not re-ask what is already answered.
4. Read `requirements/question-bank.md` (harness) - your checklist of areas and
   questions. You own the order and phrasing; the bank is the coverage guarantee.
5. Skim `requirements/templates/` (harness) so you know the shape of each deliverable.

## Step 1 - Interview

Work area by area (project brief first, then the rest). For each area:

- Summarise what you already know from intake docs and earlier answers.
- Ask the **smallest set of questions** that closes the real gaps for that area.
  Batch related questions. Prefer `AskUserQuestion` for choices with a small set
  of sensible options (extract mode, load pattern, target platform, orchestrator,
  cadence, PII yes/no). Use plain prose for open-ended things (business goal,
  known quirks, transformation logic).
- Offer a sensible default and say so ("I'll assume daily batch unless you tell
  me otherwise"). Let the user answer "use your judgement" - then record the
  assumption explicitly.
- Never ask more than ~5 questions in one turn. It is fine to take several turns.

Cover, at minimum, these areas (full detail in the question bank):

| # | Area | Core things to pin down |
|---|------|-------------------------|
| 00 | Project brief | business goal, stakeholders, success criteria, scope in/out, timeline, budget/skill constraints |
| 01 | Source systems | per source: type (sql / csv / bigquery / api / other), how reached, auth approach, objects, volume, extract mode (full / incremental / CDC / file-arrival), watermark, format/encoding, known quirks, cadence |
| 02 | Targets & loading | target platform, load pattern (append / upsert / SCD2 / truncate-reload), staging/landing zone, partitioning, file format, idempotency & replay |
| 03 | Transformations | cleansing, standardisation, dedup, joins/enrichment, derived fields, business rules, historisation (SCD), aggregation, surrogate keys, ETL vs ELT (where transforms run) |
| 04 | Data quality | which DQ dimensions to enforce, rule severity, fail vs quarantine vs fix-in-place, thresholds, DQ reporting & ownership |
| 05 | Reconciliation | row counts, control totals, financial balancing, source-to-target checks, tolerances, what a failure blocks |
| 06 | Lineage & governance | lineage granularity (table / column), catalog, ownership, glossary, audit/metadata retention |
| 07 | Scheduling & orchestration | cadence, deadlines/SLA, dependencies, orchestrator (Airflow / Dagster / Prefect / cron / ADF / other), retries, backfill, alerting |
| 08 | Security & compliance | PII/PHI classification, masking/tokenisation, encryption, secret management, access control, regulation (GDPR / HIPAA / SOX / other), retention |
| 09 | Non-functional | volume & scale, latency target, cost limits, environments (dev/test/prod), CI/CD, observability, DR/recovery, team skills, tech constraints |
| 10 | Platform, transformation framework & deployment | target engine(s) & portability (Snowflake / Databricks / BigQuery / Redshift / ...), transformation tool (dbt Core/Cloud, adapter, model layers, materialisations, snapshots, tests, packages), Infrastructure as Code (Terraform / OpenTofu / Pulumi, what it manages, state backend, env isolation), deployment & release (CI/CD tool, plan/apply + dbt build stages, promotion flow, rollback), environment topology |

Default stack assumption (state it, let the user override): a **warehouse-agnostic
target** reached through a **dbt** project (one adapter today, kept swappable),
provisioned and deployed with **Terraform** via a CI/CD pipeline that runs
`terraform plan/apply` + `dbt build`. If the user has no opinion, record this as
the assumption for area 10 rather than leaving it blank.

If the user says an area does not apply, record that ("No reconciliation
required - single low-criticality feed") rather than dropping it silently.

## Step 2 - Write the deliverables

When coverage is good enough for a first design pass (not every blank filled -
enough to architect against), write to `<WS>/requirements/`:

- `00-project-brief.md` ... `10-platform-and-deployment.md` - one file per area,
  based on the matching template in the harness `requirements/templates/`. Fill
  what you learned. Mark anything still unknown as
  `TBD - see 99-open-questions.md (Q<n>)`.
- `README.md` - a short index: project name, one-paragraph summary, the list of
  requirement files, count of open questions, date.
- `99-open-questions.md` - every gap, assumption, and decision still owed by the
  user, numbered, each with: the question, why it matters, your interim
  assumption, and who can answer it.

You may run the `requirements-synthesizer` subagent to draft these files from the
interview notes if the interview was long - pass it `<WS>` explicitly. You remain
responsible for a final read-through with the user.

## Step 3 - Close out

1. Update `<WS>/progress.json`:
   - `project_name`, `updated` (today's date),
   - `phases.1_requirements.status` = `"complete"` (or `"in_progress"` if you
     stopped early), `deliverables` = the filenames you wrote,
     `open_questions_count` = N,
   - append a `history` entry `{ "date": ..., "phase": "1_requirements", "event": "..." }`.
2. Tell the user: what you captured, the biggest open questions, and that
   `/design-architecture` is the next step (Phase 2).

## Guardrails

- Never invent connection strings, credentials, hostnames, or table names. Ask.
- Secrets are described as *references* ("vault path", "env var"), never values.
- If the user pushes to skip straight to design, capture a minimal brief +
  sources + target first - Phase 2 cannot produce anything real without them.
- Never write outside `<WS>/` except to read harness templates and the question bank.
