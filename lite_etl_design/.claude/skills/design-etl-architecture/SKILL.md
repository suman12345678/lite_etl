---
name: design-etl-architecture
description: Run Phase 2 of the ETL data-harness design process - turn the Phase 1 requirement files into an architecture overview, an architecture diagram, a data-flow diagram, a data-entity (ER) diagram, component designs, a pipeline blueprint, design-decision records and a requirement-to-design traceability matrix, all written to the active project workspace's design/ folder. Use after requirements are gathered, or when the user runs "/design-architecture".
---

# design-etl-architecture  (Phase 2)

Turn requirements into a concrete, reviewable design: diagrams first, then the
written design, then proof that every requirement is covered.

## Step 0 - Resolve the workspace and check preconditions

1. Read `state/active-workspace` (harness root) -> `<WS>`. If missing or
   `<WS>/project.json` is absent, tell the user to run `/etl-new-project` and stop.
2. Read `<WS>/progress.json`. If `phases.1_requirements.status` is not
   `complete` (or at least `in_progress` with real content), stop and tell the
   user to run `/gather-requirements` first.
3. Read every file in `<WS>/requirements/` - this is your entire input. Also read
   `<WS>/requirements/99-open-questions.md`; unresolved items become explicit
   assumptions in the design, not silent guesses.
4. Skim the harness `design/templates/` for the shape of each deliverable.

## Step 1 - Decide the shape

Before drawing anything, settle the load-bearing choices and be ready to justify
each from a specific requirement:

- **ETL vs ELT** - where transformations run (in an engine vs in the target
  warehouse). Driven by target platform, volume, team skills, cost.
- **Batch vs micro-batch vs streaming** per source - driven by SLA and source
  capability (CDC? file-arrival?).
- **Zone model** - raw / landing -> cleansed / staging -> curated / serving.
- **Orchestration** - the orchestrator named in requirements, or a recommendation
  with rationale.
- **Storage & formats** - landing format, table format, partitioning key.
- **Idempotency & replay** strategy - run ids, watermarks, backfill.
- **Transformation framework & warehouse portability** - the tool (dbt Core/Cloud
  assumed unless `10` says otherwise), the adapter(s), model layers
  (staging/intermediate/marts or bronze/silver/gold), materialisation &
  incremental strategy, SCD2 via snapshots, and how engine-specific SQL is
  contained. Driven by `10` and `03`.
- **Infrastructure & deployment** - IaC tool (Terraform assumed unless `10` says
  otherwise), what it provisions, state backend, the CI/CD stages
  (`terraform plan/apply` + `dbt build`), and the dev -> test -> prod promotion
  flow. Driven by `10` and `09`.

If a choice cannot be made because a requirement is missing, record it as a
design assumption tied to an open question - do not stall.

## Step 2 - Produce the deliverables

Write all of these to `<WS>/design/`, from the matching harness templates:

| File | What it contains |
|------|------------------|
| `architecture-overview.md` | Narrative: chosen approach and why, the component inventory, technology choices each traced to a requirement, environments, cross-cutting concerns (DQ, reconciliation, lineage, security, observability). |
| `architecture-diagram.md` | A Mermaid `flowchart` of the whole harness: sources -> extract -> landing -> transform -> DQ + reconciliation gate -> load -> serving, with the orchestration and observability planes shown. |
| `data-flow-diagram.md` | Mermaid diagram(s) of how data moves per source and per zone (raw -> cleansed -> curated), showing batch vs stream and where DQ/recon checkpoints sit. |
| `data-entity-diagram.md` | Mermaid `erDiagram` of the target model (dimensions/facts or normalised entities) with keys, relationships and SCD columns, plus key staging entities. |
| `component-design.md` | Per component (extractor, landing writer, transformer / dbt runner, DQ engine, reconciliation engine, loader, orchestration, lineage/metadata, secrets, IaC / deploy): responsibility, inputs, outputs, config, failure modes, idempotency. |
| `transformation-design.md` | The dbt project blueprint (or the equivalent for a non-dbt tool): project layout, layer model, sources & freshness, materialisation & incremental strategy, SCD2 snapshots, DQ-as-tests mapped to `04`, reconciliation hooks, packages/macros/seeds, docs & exposures, the `dbt build` run interface and slim-CI selector. |
| `deployment-and-iac.md` | The Terraform (or equivalent) module layout, what IaC owns vs not, state backend & env isolation, the CI/CD deployment pipeline (`lint -> validate -> plan -> apply -> dbt build -> promote`) as a Mermaid flow, promotion & versioning, rollback, drift detection, and the env topology table. |
| `pipeline-blueprint.md` | The DAG: task list, dependencies, trigger/cadence, retry policy, backfill approach, the reconciliation gate that blocks publish, alert points. A Mermaid DAG sketch. Show where `dbt build` sits and keep the data pipeline distinct from the deploy pipeline in `deployment-and-iac.md`. |
| `design-decisions.md` | ADR-style records: decision, context, options considered, choice, consequences. One per load-bearing choice from Step 1 - including transformation framework (dbt vs alternatives), IaC tool, single-adapter vs multi-engine portability, materialisation strategy, and the CI/CD promotion model. |
| `traceability-matrix.md` | A table: each requirement (by file + item) -> the design element(s) that satisfy it -> status (covered / partial / deferred). Every requirement file must appear. |
| `README.md` | Index of the above with a one-line summary of the design and the date. |

Diagram rules:

- Use Mermaid fenced blocks (```mermaid) so they render in GitHub and artifacts.
- Keep each diagram to one readable screen; split rather than cram.
- Label edges with what flows (dataset, control signal, metrics), not just arrows.
- Names in the ER diagram must match names used in `<WS>/requirements/03-transformations.md`
  and `<WS>/requirements/02-targets-and-loading.md`.

For the heavy synthesis you may delegate to the `solution-architect` subagent:
pass it `<WS>` and this template list, have it return drafts, then review and
land them yourself. Keep the interactive review on the main thread.

## Step 3 - Review with the user

Present: the approach in a few sentences, the diagrams, and the top design
decisions and assumptions. Ask for corrections. Revise the files.

## Step 4 - Close out

Update `<WS>/progress.json`: `phases.2_architecture.status`, `deliverables` =
filenames written, `updated` = today, append a `history` entry. Tell the user
Phase 3 (build & test) is the next step and is not built yet.

## Guardrails

- Every technology or pattern choice needs a one-line "because <requirement>".
- Do not design components for requirements that were explicitly out of scope.
- If requirements and a good design genuinely conflict, surface it as a decision
  for the user, with options - do not quietly override the requirement.
- Never write outside `<WS>/` except to read harness templates.
