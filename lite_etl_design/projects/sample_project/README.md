# sample_project - Meridian Trust Regulatory & Risk Data Harness (DEMO)

A worked example produced **entirely with the lite-etl-design harness**, kept as a
demo of how the harness is used. The client, the systems, and every number here
are **fictional**.

---

## 1. The scenario (fictional)

**Meridian Trust Bank** assembles Basel III / BCBS 239 regulatory data and the
AML feed by hand from three system exports plus spreadsheets. Month-end close
takes 9 days; the last two regulatory submissions were re-filed after
reconciliation breaks. They want a governed T+1 pipeline that lands 5 sources
(Oracle core banking, a daily card-processor SFTP file, GL balances in BigQuery,
ECB FX rates, a SQL Server CRM) into **Snowflake**, enforces data-quality and
reconciliation controls, and publishes a trusted `CURATED` layer for the 07:00
CET regulatory extract and Finance close - with column-level lineage and GDPR
treatment of customer data.

Full input: [`intake/meridian-trust-rfp-extract.md`](intake/meridian-trust-rfp-extract.md).

---

## 2. How the harness was used (the actual session, in order)

| # | Command run | Harness piece it triggered | What it did | Output |
|---|-------------|----------------------------|-------------|--------|
| 0 | `/etl-new-project sample_project` | inline command | scaffolded this workspace (`intake/ requirements/ design/ notes/`, `project.json`, `progress.json`) and set it active in `state/active-workspace` | this folder |
| 1 | *(dropped a file)* | - | put the client's RFP/discovery notes in `intake/` so the interview would read them first | [`intake/meridian-trust-rfp-extract.md`](intake/meridian-trust-rfp-extract.md) |
| 2 | `/gather-requirements` | skill **`gather-etl-requirements`** (interactive, main thread) | read the intake doc + the harness `question-bank.md`; interviewed across all 10 areas - **lifting known facts from the intake doc, asking `AskUserQuestion` for decisions** (extract mode, load patterns, ETL-vs-ELT, recon behaviour, orchestrator, lineage granularity), **prose for open points** (business goal, file quirks, PII rules), recording **"use your judgement"** calls as explicit assumptions | [`requirements/00`..`09`](requirements/) + [`requirements/README.md`](requirements/README.md) + [`requirements/99-open-questions.md`](requirements/99-open-questions.md) ; `progress.json` phase 1 → complete |
| 3 | *(client answered Q2 & Q4)* | - | auto-publish on recon PASS approved; DPO approved the crypto-shred erasure approach | notes below |
| 4 | `/finalize-requirements` | skill **`gather-etl-requirements`**, Step 2 onward (no re-interview) | folded the two answers in, bumped `00`, `07`, `08`, `99` to v1.1 | updated requirement files |
| 5 | `/design-architecture` | skill **`design-etl-architecture`** | read every `requirements/*` file (incl. `99-open-questions.md` → design assumptions); settled the load-bearing choices; wrote the design set with Mermaid diagrams; built the traceability matrix so every requirement maps to a design element | [`design/`](design/) (9 files) ; `progress.json` phase 2 → complete |
| — | `/etl-design-status` (any time) | inline command | prints: active project, phase, deliverable counts, next command | (console only) |
| — | *(new session)* | **SessionStart hook** `session_context.py` | one-line banner: `active project: Meridian Trust… phases: 1_requirements=complete \| 2_architecture=complete …` | (console only) |

A fuller transcript of step 2 - which questions were multiple-choice vs prose,
and every "use your judgement" assumption - is in
[`notes/interview-highlights.md`](notes/interview-highlights.md).

---

## 3. What each harness building block did here

- **Slash commands** (`/etl-new-project`, `/gather-requirements`,
  `/finalize-requirements`, `/design-architecture`, `/etl-design-status`) were the
  only things typed. Each is a thin prompt that resolves this workspace from
  `state/active-workspace` and invokes a skill.
- **Skill `gather-etl-requirements`** ran on the **main thread** because it had to
  interview a person. It owns the 10-area coverage, the ask-only-the-gaps
  behaviour, and writing `requirements/`.
- **Skill `design-etl-architecture`** turned `requirements/` into `design/`,
  including the 3 Mermaid diagrams and the requirement→design traceability matrix.
- **`AskUserQuestion` tool** was used for the ~9 decision points (see the notes
  file). Everything open-ended stayed a normal conversation.
- **Subagents** (`requirements-synthesizer`, `solution-architect`) were **not
  needed** for a project this size - the skills wrote the files directly. On a
  bigger engagement the skills would hand the drafting to these and keep the main
  thread for review.
- **SessionStart hook** printed where the project stood at the start of each
  session, reading this workspace's `progress.json`.
- **Harness templates** (`requirements/templates/`, `design/templates/` in the
  harness root) were the skeletons every file here was filled from - they are
  never edited per project.

---

## 4. What's in this workspace

```
sample_project/
├── project.json                 name, created date, which harness built it
├── progress.json                phase tracker (1 & 2 complete; 3-5 planned)
├── README.md                    this file
├── intake/
│   └── meridian-trust-rfp-extract.md      client's raw notes (the interview's starting point)
├── requirements/                Phase 1 output - one file per area
│   ├── README.md                index + headline per file
│   ├── 00-project-brief.md      goal, stakeholders, success criteria, scope, constraints
│   ├── 01-source-systems.md     5 sources: type, reach, auth ref, mode, volume, quirks
│   ├── 02-targets-and-loading.md  Snowflake zones, SCD2/snapshot/append patterns, idempotency, backfill
│   ├── 03-transformations.md    ETL/ELT split, per-entity rules, reference data, keys
│   ├── 04-data-quality.md       7 dimensions, concrete rules, thresholds, reporting
│   ├── 05-reconciliation.md     row counts, control totals, GL balance & tie-out, the hard gate
│   ├── 06-lineage-and-governance.md  column-level lineage, DataHub, 7-year audit, contracts
│   ├── 07-scheduling-and-orchestration.md  MWAA DAGs, SLA chain, retries, backfill, alerting
│   ├── 08-security-and-compliance.md  PAN handling, PII tokenisation, CURATED_SENSITIVE, KMS, erasure
│   ├── 09-non-functional.md     scale, cost ceiling, environments, CI/CD, observability, DR
│   └── 99-open-questions.md     5 raised, 2 answered, 3 carried into design
├── design/                      Phase 2 output
│   ├── README.md                one-line design + index
│   ├── architecture-overview.md  approach + 15-component inventory, each "because <requirement>"
│   ├── architecture-diagram.md   Mermaid system context
│   ├── data-flow-diagram.md      Mermaid per-source flows + zone contract + checkpoints
│   ├── data-entity-diagram.md    Mermaid ER (CURATED model + staging)
│   ├── component-design.md       responsibilities / interfaces / failure modes / idempotency
│   ├── pipeline-blueprint.md     Mermaid DAGs, task table, gate + backfill + alert policies, SLA chain
│   ├── design-decisions.md       ADR-001..005 + 3 open decisions
│   └── traceability-matrix.md    every requirement → design element → covered/partial/deferred
└── notes/
    └── interview-highlights.md   how the interview ran (MCQ vs prose, assumptions)
```

---

## 5. What a real engagement would do next (not built by this harness yet)

- **Step 3 - Build & test:** scaffold the components in `design/component-design.md`
  (extractors, card parser, tokeniser, DQ engine, reconciliation engine, dbt
  models) with unit tests against fixtures.
- **Step 4 - Pipeline & Git:** Airflow DAGs, environment config, repo layout,
  push.
- **Step 5 - Full testing & hardening:** integration + contract tests, DQ
  behaviour matrices, reconciliation fixtures, CI gates, observability wiring,
  security review, runbook, backfill drill.

See [`../../docs/process-overview.md`](../../docs/process-overview.md).

> **Note:** this demo was built with an earlier version of the harness, before
> the `10-platform-and-deployment` requirement area and the
> `transformation-design.md` / `deployment-and-iac.md` design deliverables were
> added. [`../sample_project_2/`](../sample_project_2/README.md) is the worked
> example that exercises those (Databricks + dbt + Terraform + Dagster).

---

## 6. Reproduce this demo yourself

From the harness root (`lite_etl_design/`), in Claude Code:

```
/etl-new-project sample_project_2
# copy intake/meridian-trust-rfp-extract.md into projects/sample_project_2/intake/
/gather-requirements          # answer the interview (or say "use your judgement")
/finalize-requirements        # after resolving any open questions
/design-architecture
/etl-design-status
```

Everything in this folder is the output of those five commands.
