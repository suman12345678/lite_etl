# Design decisions (ADR log)

> One record per load-bearing choice. Short. Link the requirement(s) that force
> or motivate it.

## ADR-001: `<title, e.g. ELT in the warehouse rather than a Spark ETL layer>`

- **Status:** proposed / accepted / superseded
- **Date:**
- **Context:** what in the requirements creates this decision (cite file + item)
- **Options considered:**
  1. _option_ - pros / cons
  2. _option_ - pros / cons
- **Decision:** _the choice_
- **Consequences:** what becomes easy, what becomes hard, what we now must also do
- **Revisit if:** _the condition that would reopen this_

---

## Decisions to record (typical set)

- ETL vs ELT and the transformation engine
- Transformation framework (dbt Core vs dbt Cloud vs SQLMesh vs hand-SQL vs Spark)
- Warehouse engine choice and single-adapter vs multi-engine portability
- dbt materialisation & incremental strategy; SCD2 via snapshots vs hand-rolled
- Processing style per source (batch / micro-batch / streaming)
- Zone model and storage layout
- Landing and target table formats + partitioning key
- Load pattern per target entity (append / upsert / SCD2 / ...)
- Orchestrator choice
- Idempotency / replay / watermark model
- Reconciliation gate strictness
- Secret-management mechanism
- IaC tool (Terraform vs OpenTofu vs Pulumi vs CDK) and what it owns vs dbt
- Terraform state backend & environment isolation model
- CI/CD promotion model (auto vs manual gates, slim CI, what artefact is promoted)
- Environment & promotion strategy

## Open decisions (need a user answer)

| # | Decision | Options | Blocking? | Linked Q# |
|---|----------|---------|-----------|-----------|
| | | | | |
