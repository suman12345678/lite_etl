# design/ (harness) - Phase 2 templates shared across all projects

This folder holds the **reusable** Phase 2 templates. It is part of the harness,
not part of any one project.

| Item | Purpose |
|------|---------|
| `templates/` | Blank shapes for each design deliverable, including skeleton Mermaid diagrams. The `design-etl-architecture` skill copies these into a project's `design/` folder and fills them. |

## What Phase 2 produces (into `<workspace>/design/`)

| File | Contents |
|------|----------|
| `architecture-overview.md` | Chosen approach and why, component inventory, environments, cross-cutting concerns, assumptions, out-of-scope. |
| `architecture-diagram.md` | Mermaid flowchart of the whole harness. |
| `data-flow-diagram.md` | Mermaid per-source flow through the zones with DQ/recon checkpoints. |
| `data-entity-diagram.md` | Mermaid ER diagram of target + staging entities, keys, SCD, lineage columns. |
| `component-design.md` | Per-component responsibility, interfaces, config, failure modes, idempotency. |
| `transformation-design.md` | dbt project blueprint: layers, sources & freshness, materialisation & incremental strategy, SCD2 snapshots, DQ-as-tests, packages, docs & exposures, the `dbt build` run interface. |
| `deployment-and-iac.md` | Terraform (or equivalent) module layout, what IaC owns, state backend, env isolation, the CI/CD `plan -> apply -> dbt build -> promote` pipeline (Mermaid), rollback, drift, env topology. |
| `pipeline-blueprint.md` | Task DAG, retry/backfill policy, the reconciliation gate, alert points. |
| `design-decisions.md` | ADR-style records for every load-bearing choice; open decisions list. |
| `traceability-matrix.md` | Every Phase 1 requirement -> design element -> covered/partial/deferred. |
| `README.md` | Index + one-line design summary + date. |

Diagrams are Mermaid so they render in GitHub, most Markdown viewers, and Claude
artifacts. Paste any block into `mermaid.live` to tweak it visually.

Run `/design-architecture` after Phase 1 is done. See `../MAP.md` for the full flow.
