# Design - Meridian Trust Regulatory & Risk Data Harness (DEMO)

**One-line design:** split ETL (Python: extract, parse, drop full PAN, tokenise
PII) / ELT (dbt on Snowflake: model, SCD2, FX conversion, DQ, reconciliation),
across an immutable `S3 → RAW → STAGING → CURATED (+ CURATED_SENSITIVE)` zone
model, orchestrated by Airflow/MWAA, with a **hard reconciliation gate** that
blocks publish and column-level lineage into DataHub.

**Produced by:** the `design-etl-architecture` skill (`/design-architecture`) on
2026-09-03 from [`../requirements/`](../requirements/). Fictional client.

## Files

| File | Contents |
|------|----------|
| [architecture-overview.md](architecture-overview.md) | approach + rationale, 15-component inventory (each traced to a requirement), environments, cross-cutting concerns, the 3 open design assumptions |
| [architecture-diagram.md](architecture-diagram.md) | Mermaid system-context flowchart: 5 sources → ETL → S3 → Snowflake zones → DQ → reconciliation gate → CURATED → regulatory extract / Finance |
| [data-flow-diagram.md](data-flow-diagram.md) | Mermaid per-shape flows: file-arrival (cards), incremental (core banking / CRM), daily snapshot (GL), reference + carry-forward (FX); zone contract; checkpoints |
| [data-entity-diagram.md](data-entity-diagram.md) | Mermaid ER: CURATED model (DIM_ACCOUNT/CUSTOMER SCD2, FACT_CARD_TXN/GL_BALANCE/ACCOUNT_BALANCE_DAILY, DIM_FX_RATE, CUSTOMER_SENSITIVE) + key STAGING entities |
| [component-design.md](component-design.md) | per-component responsibility / inputs / outputs / failure modes / idempotency for the risk-carrying components |
| [pipeline-blueprint.md](pipeline-blueprint.md) | per-source DAG + gated `curated_build` DAG (Mermaid), task table, backfill + gate + alert policies, the 03:30→07:00 SLA chain |
| [design-decisions.md](design-decisions.md) | ADR-001..005 (ETL/ELT split, immutable landing, hard recon gate, MWAA, PII segregation) + 3 open decisions carried into build |
| [traceability-matrix.md](traceability-matrix.md) | every requirement item → design element → covered / partial / deferred, + gaps |

## Status

Phase 2 **complete**. 3 items are `partial` (cost validation, sub-ledger tie-out,
BCBS 239 constraints - all with a named follow-up). Next in a real engagement:
Phase 3 (build & test the components) - not part of this harness yet.
