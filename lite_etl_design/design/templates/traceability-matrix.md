# Requirement -> design traceability matrix

> Coverage proof. Every requirement file from Phase 1 must appear. One row per
> requirement item (or per coherent group). Status: **covered** / **partial** /
> **deferred** (with reason).

| Req file | Item | Design element(s) that satisfy it | Status | Notes |
|----------|------|-----------------------------------|--------|-------|
| 00-project-brief | success criterion 1 | | | |
| 01-source-systems | source `<slug>` extract mode | Extractor design; data-flow diagram | | |
| 02-targets-and-loading | load pattern for `<table>` | Loader design; ER diagram | | |
| 03-transformations | historisation of `<entity>` | Transformer design; ER (SCD2 cols) | | |
| 04-data-quality | reject threshold | DQ engine design; pipeline gate | | |
| 05-reconciliation | control totals | Reconciliation engine; pipeline gate | | |
| 06-lineage-and-governance | column-level lineage | Lineage component; ER lineage cols | | |
| 07-scheduling-and-orchestration | SLA 06:00 UTC | Orchestrator design; pipeline blueprint | | |
| 08-security-and-compliance | mask `<field>` | Security component; data-flow checkpoint | | |
| 09-non-functional | environments | Architecture overview s.3; deployment-and-iac | | |
| 10-platform-and-deployment | target engine / portability | Architecture overview s.1; transformation-design | | |
| 10-platform-and-deployment | dbt layers / materialisation / tests | transformation-design | | |
| 10-platform-and-deployment | IaC scope + state backend | deployment-and-iac s.1-3 | | |
| 10-platform-and-deployment | CI/CD promotion + rollback | deployment-and-iac s.4-6 | | |

## Gaps

| Requirement not covered | Why | Proposed follow-up |
|-------------------------|-----|--------------------|
| | | |
