# Architecture overview

> Phase 2 deliverable. Written by `design-etl-architecture` from the workspace's
> `requirements/` folder. Every choice carries a "because <requirement>".

- **Project:**
- **Date / version:**
- **Requirements baseline:** (which requirement files + version this is built on)

## 1. Approach

- **ETL vs ELT:** _choice_ - because _requirement_
- **Processing style per source:** batch / micro-batch / streaming - because _..._
- **Zone model:** raw/landing -> cleansed/staging -> curated/serving - what lives in each
- **Orchestration:** _tool_ - because _..._
- **Storage & formats:** landing format, target table format, partition key - because _..._
- **Idempotency & replay:** run-id + watermark model - because _..._
- **Transformation framework:** dbt Core/Cloud / SQLMesh / ... + adapter(s);
  layer model (staging -> intermediate -> marts) - because `10` / `03`. Detail in
  `transformation-design.md`.
- **Warehouse portability:** single adapter / kept swappable / multi-engine; where
  engine-specific SQL is confined - because `10`.
- **Infrastructure as Code:** Terraform / OpenTofu / ... - what it provisions,
  state backend - because `10`. Detail in `deployment-and-iac.md`.
- **Deployment & promotion:** CI/CD tool; `plan/apply` + `dbt build`; dev -> test
  -> prod flow - because `10` / `09`.

## 2. Component inventory

| Component | Responsibility | Technology | Because (requirement) |
|-----------|----------------|------------|-----------------------|
| Extractor(s) | pull from each source type | | 01 |
| Landing writer | atomic write to the landing zone | | 02 |
| Transformer / dbt runner | cleanse / standardise / historise (dbt models + snapshots) | dbt | 03, 10 |
| DQ engine | apply data-quality rules, route rows (dbt tests + engine) | dbt tests | 04, 10 |
| Reconciliation engine | prove the load, gate publish | | 05 |
| Loader | land -> target table, per load pattern | | 02 |
| Orchestrator | schedule, dependencies, retries, backfill | | 07 |
| Lineage / metadata | run manifests, dbt manifest, catalog registration | | 06 |
| Secrets / security | resolve references, mask, encrypt | | 08 |
| Observability | logs, metrics, alerts, dashboards | | 09 |
| IaC / provisioning | Terraform modules: warehouse objects, grants, compute, storage, orchestrator infra | Terraform | 10 |
| CI/CD deploy | lint -> validate -> plan -> apply -> `dbt build` -> promote | | 10, 09 |

## 3. Environments

_dev / test / prod - accounts, promotion flow, test data strategy (from 09)._

## 4. Cross-cutting concerns

- **Data quality:** where checks run (dbt tests + engine), fail vs quarantine, thresholds
- **Reconciliation:** which checks, tolerances, what a FAIL blocks
- **Lineage:** granularity, capture mechanism (run manifests + dbt manifest), catalog
- **Security:** classification, masking points, secret resolution, encryption
- **Observability:** metric set, alert triggers, healthy definition
- **Transformation & portability:** dbt project shape, adapter, how engine-specific
  SQL is contained - see `transformation-design.md`
- **Deployment & IaC:** what Terraform owns, state backend, CI/CD promotion flow,
  rollback - see `deployment-and-iac.md`

## 5. Open design assumptions

_Each unresolved open question from Phase 1 and the assumption the design makes._

| Ref (Q#) | Assumption | Impact if wrong |
|----------|------------|-----------------|
| | | |

## 6. Out of scope

_Explicitly not designed, per the brief._
