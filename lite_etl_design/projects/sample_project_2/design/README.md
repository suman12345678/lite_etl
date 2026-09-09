# Design - Northwind Commerce (DEMO)

**One-line design:** lightweight Python extractors land 6 sources raw in a
Databricks **`bronze`** zone; **dbt Core** (`dbt-databricks`) transforms
`bronze -> silver -> gold`/`gold_pii` (staging views, ephemeral intermediates,
snapshot-backed SCD2 dims, incremental-`merge` facts); a **hard reconciliation
gate** implemented as a blocking **Dagster** asset check stops any unreconciled
publish; **Terraform** provisions every environment and **GitHub Actions**
promotes the same git SHA + dbt manifest dev -> stg -> prd.

**Produced by:** the `design-etl-architecture` skill (`/design-architecture`) on
2026-09-09 from [`../requirements/`](../requirements/). Fictional client.

## Files

| File | Contents |
|------|----------|
| [architecture-overview.md](architecture-overview.md) | approach + rationale, 12-component inventory (each traced to a requirement), environments, cross-cutting concerns, the 3 open design assumptions |
| [architecture-diagram.md](architecture-diagram.md) | Mermaid system context: 6 sources -> extractors -> bronze/silver/gold -> reconcile gate -> gold -> consumers, plus the Dagster control plane and the Terraform + GitHub Actions build/deploy plane |
| [data-flow-diagram.md](data-flow-diagram.md) | Mermaid per-shape flows: incremental pull, file-arrival (POS supersede), prior-day snapshot (GA4), reference carry-forward (FX); zone contract; checkpoints |
| [data-entity-diagram.md](data-entity-diagram.md) | Mermaid ER: `gold` model (SCD2 dims, fact grains), `gold_pii`, key `silver` staging entities |
| [component-design.md](component-design.md) | per-component responsibility / inputs / outputs / failure modes / idempotency for the risk-carrying components |
| [transformation-design.md](transformation-design.md) | the dbt project blueprint: layout, layer model, sources & freshness, materialisation & incremental strategy, snapshots, DQ-as-tests mapped to area 04, reconciliation hooks, packages/macros/seeds, docs & exposures, the `dbt build` run interface + slim-CI selector |
| [deployment-and-iac.md](deployment-and-iac.md) | Terraform module layout, what IaC owns vs dbt, S3+DynamoDB state, dir-per-env isolation, the GitHub Actions `lint -> validate -> plan -> apply -> dbt build -> promote` pipeline (Mermaid), promotion & versioning, rollback, drift, env topology |
| [pipeline-blueprint.md](pipeline-blueprint.md) | the Dagster data-pipeline asset graph (Mermaid), asset table, backfill + gate + alert policies, the 05:00 -> 06:00 UTC SLA chain |
| [design-decisions.md](design-decisions.md) | ADR-001..006 (ELT+dbt, dbt Core not Cloud, single-adapter portability, Terraform split, Dagster + asset-check gate, PII split) + 3 open decisions |
| [traceability-matrix.md](traceability-matrix.md) | every requirement item -> design element -> covered / partial / deferred, + gaps |

## Status

Phase 2 **complete**. 4 items are `partial` (24-month backfill depth, wholesale
recognition grain + its GMV recon, peak-volume cost validation - each with a
named follow-up). 3 open decisions (Q2/Q3/Q4) carried into build. Next in a real
engagement: Phase 3 (build & test the extractors + the dbt project) - not part
of this harness yet.
