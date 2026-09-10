# Build plan - Northwind Commerce (DEMO)

> Phase 3 deliverable. Written by `build-etl-components` from
> [`../design/`](../design/) on 2026-09-09. The order components are built, what
> "done" means for each, and how to run them locally. Fictional client.

- **Project:** Northwind Commerce - Unified Retail Analytics Harness
- **Date / version:** 2026-09-09 / v1.0
- **Design baseline:** `design/` v1.0 (`architecture-overview.md` §2 component
  inventory, `component-design.md`, `transformation-design.md`,
  `deployment-and-iac.md`, `data-entity-diagram.md`, `pipeline-blueprint.md`)
- **Repo location:** `build/repo/` (mono-repo scaffold) -> promoted to the real
  `northwind-data` repo in Phase 4
- **Language:** Python 3.12 (extractors + engines), dbt Core 1.8 + `dbt-databricks`
  (transform), `dbt-duckdb` for local tests. Task runner: `make`.

## 1. Build order

Build one component at a time, lowest dependency first. Each must pass its unit
tests (`make test-<slug>`) against fixtures before the next starts.

| # | Component (slug) | Depends on | Design ref | Buildsheet |
|---|------------------|-----------|-----------|-----------|
| 1 | `config` - config loader + `_state.watermarks` state store | - | component-design `state store`; `10` config layering | [component-buildsheet-config.md](component-buildsheet-config.md) |
| 2 | `secrets` - `secret-scope://` resolver + PII hashing helper | 1 | component-design `secrets & security`; `08` | [component-buildsheet-secrets.md](component-buildsheet-secrets.md) |
| 3 | `extractor` - the extractor framework + 6 source modules (oltp / shopify / pos / salesforce / ga4 / fx) | 1, 2 | component-design `extractor`; `01` | [component-buildsheet-extractor.md](component-buildsheet-extractor.md) |
| 4 | `landing` - atomic Delta write, manifest, `_run_id` tagging, POS supersede | 3 | component-design `landing writer` (folded into extractor); `02` | [component-buildsheet-landing.md](component-buildsheet-landing.md) |
| 5 | `dbt` - the dbt project (staging -> intermediate -> marts + snapshots + seeds + all DQ tests) | 4 | transformation-design; `03`, `04` | [component-buildsheet-dbt-runner.md](component-buildsheet-dbt-runner.md) + [dbt-project-scaffold.md](dbt-project-scaffold.md) |
| 6 | `reconciliation` - `tag:recon` dbt tests + Python manifest compare, PASS/FAIL verdict | 5 | component-design `reconciliation engine`; `05` | [component-buildsheet-reconciliation.md](component-buildsheet-reconciliation.md) |
| 7 | `publisher` - `gold`/`gold_pii` transaction, UC register, watermark advance | 6 | component-design `publisher`; `02`, `06` | [component-buildsheet-publisher.md](component-buildsheet-publisher.md) |
| 8 | `lineage` - run manifest + dbt manifest + OpenLineage emitter | 4, 5 | component-design; `06` | [component-buildsheet-lineage.md](component-buildsheet-lineage.md) |
| 9 | `observability` - metrics + structured logging hooks | all | component-design `observability`; `09` | [component-buildsheet-observability.md](component-buildsheet-observability.md) |

Deferred to Phase 4 (`/assemble-pipeline`): `orchestrator` (Dagster asset graph),
`IaC / provisioning` (Terraform modules), `CI/CD deploy` (GitHub Actions). Their
component-design sections point at `deployment-and-iac.md`.

## 2. Definition of "component complete"

A component is done when **all** hold:

- [ ] Code exists in `build/repo/` at the path in its buildsheet.
- [ ] Public interface matches the buildsheet (inputs, outputs, config keys).
- [ ] Unit tests cover: happy path, each documented failure mode, idempotent
      re-run, and every edge case in `fixtures-catalog.md` for its source.
- [ ] Runs locally per `local-dev.md` with no cloud dependency (DuckDB / mock
      HTTP / sample files).
- [ ] Emits the metrics + lineage events named in `component-design.md`.
- [ ] Config-driven - no hard-coded hostnames, paths, or credentials
      (`extractors/config/<src>.yml` + `config/<env>.yml` only).
- [ ] Added to `make test` and the CI unit-test job (handed to Phase 4).

## 3. Local run

- **Prereqs:** Python 3.12, `uv`, `make`; `dbt-core` + `dbt-databricks` +
  `dbt-duckdb`; Docker optional for the Postgres integration stand-in.
- **Setup:** `make setup`
- **One component:** `make test-oltp` (etc.)
- **Full local pass:** `make test` - every component's unit tests +
  `dbt build --target ci` on DuckDB with seeds + fixtures. Must be green before
  Phase 4.

## 4. CI hook (handed to Phase 4)

- `make lint` (ruff + sqlfluff) + `make test` on every push.
- `dbt build --target ci` on the PR; slim CI (`--select state:modified+ --defer`)
  once a prod manifest exists.
- Coverage threshold: **80%** on `extractors/`, `recon/`, `publish/` logic.
- `terraform fmt/validate/plan` added in Phase 4.

## 5. Open items

| # | Item | Blocks which component | Owner |
|---|------|------------------------|-------|
| O1 | Q3 (Dagster Cloud vs OSS) - only affects Phase 4 `orchestrator`, not Phase 3 | - | InfoSec |
| O2 | Q4 (wholesale recognition grain) - `int_sales__order_wholesale` + `fct_wholesale_opportunity` stubs use fulfillment grain with a `TODO` | `dbt` (5) | Finance |
| O3 | GA4 aggregation SQL for the BigQuery extract job is a `TODO` in `extractors/ga4.py` - needs the GA4 event schema | `extractor` (3) | Marketing |
| O4 | Real column lists for OLTP tables - `_oltp__sources.yml` has the known columns from `01`; confirm against the live ERD in `intake/` | `dbt` (5) | Commerce Platform |
