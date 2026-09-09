# sample_project_2 - Northwind Commerce Unified Retail Analytics Harness (DEMO)

A second worked example produced **entirely with the lite-etl-design harness**
(v0.2). It exists to exercise the parts of the harness that
[`../sample_project/`](../sample_project/README.md) predates - the
**`10-platform-and-deployment`** requirement area and the
**`transformation-design.md`** + **`deployment-and-iac.md`** design deliverables -
and to give you a full run to inspect. The client, the systems, and every number
here are **fictional**.

> **Different stack on purpose.** `sample_project` is Snowflake + Airflow + S3.
> This one is **Databricks lakehouse + dbt Core + Terraform + Dagster + GitHub
> Actions**, so the two together show the harness is warehouse- and
> tool-agnostic.

---

## 1. The scenario (fictional)

**Northwind Commerce** is a UK omnichannel retailer - 60 stores, a Shopify
online store, a B2B wholesale arm, ~2M customers. Sales and customer data is
scattered across spreadsheets and an ageing Redshift cluster nobody trusts;
Finance and Marketing keep different numbers. They have bought Databricks and
want a governed lakehouse: land **6 sources** (Postgres OLTP, Shopify REST, store
POS CSVs on S3, Salesforce, GA4-in-BigQuery, an FX rates API), transform with
**dbt**, provision and ship everything with **Terraform + GitHub Actions**,
orchestrate with **Dagster**, and publish a reconciled `gold` layer (plus a
restricted `gold_pii`) that Looker, the Braze reverse-ETL, and the Finance close
all read from - **reconciled and published by 06:00 UTC every day**, with
column-level lineage and UK-GDPR treatment of customer PII, for under $6k/month.

Full input: [`intake/northwind-commerce-discovery.md`](intake/northwind-commerce-discovery.md).

---

## 2. How the harness was used (the actual session, in order)

| # | Command run | Harness piece it triggered | What it did | Output |
|---|-------------|----------------------------|-------------|--------|
| 0 | `/etl-new-project sample_project_2` | inline command | scaffolded this workspace (`intake/ requirements/ design/ notes/`, `project.json`, `progress.json`) and set it active in `state/active-workspace` | this folder |
| 1 | *(dropped a file)* | - | put the discovery notes in `intake/` so the interview would read them first | [`intake/northwind-commerce-discovery.md`](intake/northwind-commerce-discovery.md) |
| 2 | `/gather-requirements` | skill **`gather-etl-requirements`** (interactive, main thread) | read the intake doc + the harness `question-bank.md`; interviewed across all **11** areas - lifting known facts from intake, `AskUserQuestion` for decisions (extract modes, load patterns, ELT-vs-ETL, orchestrator, **target engine & portability, dbt layer model, IaC tool, CI/CD promotion**), prose for open points (business goal, PII rules, recon tolerances), recording "use your judgement" calls as explicit assumptions | [`requirements/00`..`10`](requirements/) + [`requirements/README.md`](requirements/README.md) + [`requirements/99-open-questions.md`](requirements/99-open-questions.md); `progress.json` phase 1 -> complete |
| 3 | *(client answered Q1 & Q5)* | - | GA4 via a scheduled extract job (not federation); `gold_pii` stays in the same catalog under UC row filter + column mask (DPO-approved) | notes in `99-open-questions.md` |
| 4 | `/finalize-requirements` | skill **`gather-etl-requirements`**, Step 2 onward (no re-interview) | folded the two answers in, bumped `00`, `08`, `10`, `99` to v1.1 | updated requirement files |
| 5 | `/design-architecture` | skill **`design-etl-architecture`** | read every `requirements/*` file (incl. `99-open-questions.md` -> design assumptions); settled the load-bearing choices **including transformation framework & warehouse portability and infrastructure & deployment**; wrote the design set with 4 Mermaid diagrams, the **dbt project blueprint** and the **Terraform + CI/CD deployment design**; built the traceability matrix | [`design/`](design/) (11 files); `progress.json` phase 2 -> complete |
| - | `/etl-design-status` (any time) | inline command | prints: active project, phase, deliverable counts, next command | (console only) |
| - | *(new session)* | **SessionStart hook** `session_context.py` | one-line banner: `active project: Northwind Commerce... phases: 1_requirements=complete \| 2_architecture=complete ...` | (console only) |

A fuller transcript of the interview - which questions were multiple-choice vs
prose, and every "use your judgement" assumption - is in
[`notes/interview-highlights.md`](notes/interview-highlights.md).

---

## 3. What each harness building block did here

- **Slash commands** (`/etl-new-project`, `/gather-requirements`,
  `/finalize-requirements`, `/design-architecture`, `/etl-design-status`) were the
  only things typed. Each resolves this workspace from `state/active-workspace`
  and invokes a skill.
- **Skill `gather-etl-requirements`** ran on the **main thread** (it interviews a
  person). It owns the 11-area coverage - area **10** is the new one: target
  engine & portability, the dbt project, Terraform / IaC, CI/CD promotion.
- **Skill `design-etl-architecture`** turned `requirements/` into `design/`,
  including `transformation-design.md` (dbt) and `deployment-and-iac.md`
  (Terraform + GitHub Actions) alongside the architecture, diagrams and
  traceability matrix.
- **`AskUserQuestion` tool** handled the ~14 decision points (see the notes
  file). Everything open-ended stayed a normal conversation.
- **Subagents** (`requirements-synthesizer`, `solution-architect`) were **not
  needed** at this size - the skills wrote the files directly.
- **SessionStart hook** printed where the project stood at the start of each
  session, reading this workspace's `progress.json`.
- **Harness templates** (`requirements/templates/00..10`, `design/templates/*` in
  the harness root) were the skeletons every file here was filled from - never
  edited per project.

---

## 4. What's in this workspace

```
sample_project_2/
├── project.json                 name, created date, which harness built it (v0.2)
├── progress.json                phase tracker (1 & 2 complete; 3-5 planned)
├── README.md                    this file
├── intake/
│   └── northwind-commerce-discovery.md      client's raw notes (the interview's starting point)
├── requirements/                Phase 1 output - one file per area (11 areas)
│   ├── README.md                index + headline per file
│   ├── 00-project-brief.md      goal, stakeholders, success criteria, scope, constraints
│   ├── 01-source-systems.md     6 sources: type, reach, auth ref, mode, volume, quirks
│   ├── 02-targets-and-loading.md  Databricks UC zones, SCD2/merge/append patterns, idempotency, backfill
│   ├── 03-transformations.md    ELT split, per-entity rules, reference data, keys
│   ├── 04-data-quality.md       7 dimensions as dbt tests, concrete rules, thresholds, reporting
│   ├── 05-reconciliation.md     row counts, per-channel GMV totals, refund balancing, the hard gate
│   ├── 06-lineage-and-governance.md  column-level lineage, Unity Catalog, 5-year audit, contracts
│   ├── 07-scheduling-and-orchestration.md  Dagster assets, S3 sensor, SLA chain, retries, backfill, alerting
│   ├── 08-security-and-compliance.md  hashed PII / gold_pii, UC row filter+mask, KMS, crypto-shred RTBF
│   ├── 09-non-functional.md     scale, $6k cost ceiling, environments, CI/CD, observability, DR
│   ├── 10-platform-and-deployment.md  Databricks + portability, dbt Core project, Terraform 1.9, GitHub Actions promotion
│   └── 99-open-questions.md     5 raised, 2 answered, 3 carried into design
├── design/                      Phase 2 output (11 files)
│   ├── README.md                one-line design + index
│   ├── architecture-overview.md  approach + 12-component inventory, each "because <requirement>"
│   ├── architecture-diagram.md   Mermaid system context incl. the build/deploy plane
│   ├── data-flow-diagram.md      Mermaid per-shape flows + zone contract + checkpoints
│   ├── data-entity-diagram.md    Mermaid ER (gold model + gold_pii + staging)
│   ├── component-design.md       responsibilities / interfaces / failure modes / idempotency
│   ├── transformation-design.md  the dbt project blueprint (layers, materialisations, snapshots, tests, run interface)
│   ├── deployment-and-iac.md     Terraform module layout + the GitHub Actions plan/apply/dbt-build/promote pipeline
│   ├── pipeline-blueprint.md     Mermaid Dagster asset graph, asset table, gate + backfill + alert policies, SLA chain
│   ├── design-decisions.md       ADR-001..006 + 3 open decisions
│   └── traceability-matrix.md    every requirement -> design element -> covered/partial/deferred
└── notes/
    └── interview-highlights.md   how the interview ran (MCQ vs prose, assumptions)
```

---

## 5. What a real engagement would do next (not built by this harness yet)

- **Step 3 - Build & test:** scaffold the extractors + the **dbt project**
  (`models/staging|intermediate|marts`, `snapshots/`, `seeds/`, `tests/recon_*`,
  `sources.yml`) with unit tests on `dbt-duckdb` and fixtures.
- **Step 4 - Pipeline & Git:** the Dagster asset code, the **Terraform** modules
  under `infra/envs/{dev,stg,prd}`, the GitHub Actions workflows
  (`plan/apply` + `dbt build` + promotion), repo layout, push.
- **Step 5 - Full testing & hardening:** integration + contract tests, DQ
  behaviour matrices, reconciliation fixtures, `dbt build` + `terraform plan` CI
  gates, drift detection, observability wiring, security review, a peak-volume
  cost dry-run, backfill + prod rollback drills.

See [`../../docs/process-overview.md`](../../docs/process-overview.md).

---

## 6. Reproduce this demo yourself

From the harness root (`lite_etl_design/`), in Claude Code:

```
/etl-new-project my_retail_test
# copy intake/northwind-commerce-discovery.md into projects/my_retail_test/intake/
/gather-requirements          # answer the interview (or say "use your judgement")
/finalize-requirements        # after resolving any open questions
/design-architecture
/etl-design-status
```

Everything in this folder is the output of those five commands.
