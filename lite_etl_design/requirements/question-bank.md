# ETL data-harness requirements - question bank

This is the **coverage checklist** for Phase 1. The interviewer (the
`gather-etl-requirements` skill) owns the order and wording and asks only what is
still unknown. Every area below must end up either answered in the workspace's
`requirements/` folder or explicitly recorded as not applicable.

Legend: **(D)** = decision, good fit for `AskUserQuestion`; **(O)** = open-ended.

---

## 00 - Project brief

- (O) What is the business goal? What decision or process does this data enable?
- (O) Who are the stakeholders / data owners / consumers?
- (O) What does "done and working" look like - measurable success criteria?
- (O) What is explicitly **in scope** and **out of scope** for this build?
- (O) Timeline / milestones? Any hard external date?
- (D) Team skill set and preferred stack (Python / SQL / Spark / dbt / cloud)?
- (O) Budget or cost ceiling? Existing platform we must use?

## 01 - Source systems  (ask per source)

- (O) Source name / slug and subject area (e.g. `finance_customers`, finance).
- (D) Source type: `sql` (which engine?) / `csv` (where dropped?) / `bigquery` /
  `rest_api` / `sftp` / `object storage` / `streaming` / other.
- (O) How is it reached - host / URL / bucket / dataset / table / query / glob?
- (D) Auth method: env var / secret manager / key file / IAM role / OAuth / none.
- (O) Which objects - table list, SQL query, file pattern, API endpoints?
- (D) Extract mode: `full` / `incremental` / `CDC` / `file-arrival`.
- (O) If incremental: watermark column and its type/timezone.
- (O) Expected volume: rows/day, GB/day, file count, peak vs average.
- (O) Refresh cadence available at source; latest data can lag by how much?
- (O) Format & encoding: delimiter, header, encoding, date/number formats, nulls.
- (O) Known quirks: trailing spaces, mixed types, partial files, late data,
  schema changes, duplicate deliveries, timezone traps.
- (O) Is there a data dictionary / sample extract available? (put it in `intake/`)

## 02 - Targets & loading

- (D) Target platform: cloud warehouse (BigQuery / Snowflake / Redshift /
  Synapse) / lakehouse (Delta / Iceberg / Hudi) / relational DB / files.
- (O) Target schema / dataset / database and naming conventions.
- (D) Load pattern per target table: `append` / `upsert (merge)` /
  `SCD type 2` / `truncate-reload` / `snapshot`.
- (O) Natural / business key and, if used, surrogate key strategy.
- (D) Is a landing / staging zone required before the target? Where?
- (O) Partitioning / clustering key; file format in the lake (Parquet default?).
- (O) Idempotency & replay: run ids, how a re-run avoids double-loading, how a
  bad load is rolled back.
- (O) Historical backfill needed at go-live? How far back?

## 03 - Transformations

- (D) ETL or ELT - do transforms run in an engine before load, or in SQL inside
  the target after load?
- (O) Cleansing: trimming, casing, whitespace, encoding fixes, type casting.
- (O) Standardisation: code/lookup mapping, units, currency, address/name norm.
- (O) Deduplication: what defines a duplicate, which record wins.
- (O) Joins / enrichment: reference data, lookups, derived attributes.
- (O) Business rules / derived measures - describe the logic or point to a spec.
- (O) Historisation: which entities need SCD2, effective dating, soft deletes.
- (O) Aggregations / rollups / snapshots to build.
- (O) Rejected-row handling: drop, quarantine, or fix-in-place.

## 04 - Data quality

- (D) Which DQ dimensions must be enforced: completeness / validity /
  uniqueness / consistency / timeliness / accuracy / referential integrity.
- (O) Concrete rules per critical field (not null, range, regex, allowed values,
  FK exists, freshness window).
- (D) On rule failure: fail the run / quarantine the row / fix-in-place / warn.
- (O) Thresholds - e.g. "fail if >0.5% of rows reject", "warn at 0.1%".
- (O) DQ reporting: who sees it, where, how often; is a DQ score tracked?
- (O) Who owns fixing bad source data?

## 05 - Reconciliation

- (D) Which checks: row counts (source vs target) / control totals (SUM/MIN/MAX
  of measures) / financial balancing (debits=credits, opening+delta=closing) /
  column hash / referential coverage / duplicate check / distribution drift.
- (O) Tolerances per check (exact match vs +/- X%).
- (D) What does a reconciliation failure do - block publish / alert only / auto
  retry?
- (O) Is there an authoritative control report to reconcile against?
- (O) Per-partition or whole-dataset reconciliation?

## 06 - Lineage & governance

- (D) Lineage granularity: dataset-level / table-level / column-level.
- (O) Catalog / metadata tool in use (DataHub / Collibra / Purview / Unity /
  Glue / none)?
- (O) Ownership model - who owns each dataset, who is on-call.
- (O) Business glossary / semantic definitions to attach.
- (O) Audit needs: retain run manifests, schema history, who-ran-what, for how long.
- (O) Change management - how schema changes get approved and communicated.

## 07 - Scheduling & orchestration

- (O) Cadence per pipeline: hourly / daily / event-driven / continuous.
- (O) Deadline / SLA - "landed and reconciled by 06:00 UTC".
- (O) Dependencies - which pipelines must finish before this one starts.
- (D) Orchestrator: Airflow / Dagster / Prefect / cron / ADF / Step Functions /
  cloud-native / to be recommended.
- (O) Retry policy: transient vs permanent errors, max attempts, backoff.
- (O) Backfill / catch-up behaviour after an outage.
- (D) Alerting channel and who is paged on failure / SLA breach.

## 08 - Security & compliance

- (D) Does the data contain PII / PHI / PCI / other sensitive classes?
- (O) Which fields, and the required treatment: mask / hash / tokenise / encrypt /
  drop / row-level filter.
- (D) Secret management: env vars / Vault / cloud secret manager / key files.
- (O) Encryption in transit and at rest - requirements and existing standards.
- (O) Access control - who may read raw vs curated; row/column-level rules.
- (D) Regulatory regime: GDPR / HIPAA / SOX / CCPA / internal only.
- (O) Data retention and deletion (right-to-be-forgotten) requirements.

## 09 - Non-functional

- (O) Total scale: number of sources, tables, total volume, growth rate.
- (O) Latency target end-to-end (source change -> visible in target).
- (O) Cost constraints / expected budget for compute + storage.
- (D) Environments: dev / test / prod - separate accounts/projects? promotion flow.
- (D) CI/CD expectations - tests on every change, deployment mechanism.
- (O) Observability - logs, metrics, dashboards, what "healthy" looks like.
- (O) DR / recovery - RPO/RTO, what happens if the platform is down for a day.
- (O) Tech constraints - approved services only, on-prem parts, network isolation.

## 10 - Platform, transformation framework & deployment

**Warehouse / engine portability**

- (D) Target engine(s): Snowflake / Databricks / BigQuery / Redshift / Synapse /
  DuckDB / other. One now, or must stay swappable, or genuinely multi-engine?
- (D) Must transformation SQL stay engine-neutral (no vendor-only syntax)?
- (O) Abstraction: dbt adapter per engine / agnostic SQL dialect / one codebase
  per engine / not required.
- (O) Engine-specific features you deliberately rely on (MERGE, clustering,
  `QUALIFY`, streams/CDC, `COPY INTO`, Delta `MERGE`, geospatial).

**Transformation framework**

- (D) Tool: dbt Core / dbt Cloud / SQLMesh / plain SQL scripts / Spark. Version?
- (O) Adapter(s): `dbt-snowflake` / `dbt-databricks` / `dbt-bigquery` / ...
- (O) Repo layout: mono-repo vs dedicated transform repo; one dbt project vs
  project-per-domain.
- (O) Model layers and the naming convention (staging -> intermediate -> marts,
  or bronze/silver/gold) and what belongs in each.
- (D) Default materialisation and per-layer policy (view / table / incremental /
  ephemeral); incremental strategy (`merge` / `insert_overwrite` / `append`) and
  `unique_key`.
- (O) History / SCD2 mechanism: dbt snapshots / `dbt_utils` / hand-rolled - for
  which entities.
- (D) Test strategy: built-in generic tests + which packages (`dbt_utils`,
  `dbt_expectations`, `elementary`) + singular tests; which gate CI vs each run.
- (O) Packages, macros, seeds (reference CSVs) kept in the repo.
- (O) `dbt docs` / exposures - where published, which downstream consumers
  declared; `source freshness` thresholds.

**Infrastructure as Code**

- (D) Tool: Terraform / OpenTofu / Pulumi / CDK / CloudFormation / Bicep / none.
- (O) What IaC manages: warehouse databases/catalogs & schemas, roles/grants,
  compute/warehouses, storage buckets & external locations, secret scopes,
  network, the orchestrator infra, CI runners, monitoring.
- (O) What is explicitly *not* in IaC (dbt-managed objects, data, break-glass).
- (O) Providers / modules used; own modules vs registry.
- (D) State backend and locking: S3+DynamoDB / GCS / Azure Blob / Terraform
  Cloud / Spacelift.
- (D) Environment isolation: workspace-per-env / dir-per-env / separate state.
- (O) Drift detection: scheduled `plan` / Terraform Cloud / driftctl - cadence,
  who is alerted.

**Deployment & release**

- (D) CI/CD tool: GitHub Actions / GitLab CI / Azure DevOps / Jenkins / dbt Cloud
  jobs.
- (O) Pipeline stages: lint -> validate/unit -> `terraform plan` + `dbt build` on
  CI schema -> review -> `terraform apply` + `dbt build` on merge -> promote.
- (D) Promotion flow dev -> test -> prod: automatic vs manual approval per hop;
  what artefact is promoted (git SHA / dbt manifest / image).
- (O) Slim CI via dbt `state:modified` / `--defer`? Versioning (tags / semver)?
- (D) Rollback: revert-and-redeploy / `terraform apply` previous SHA / warehouse
  time-travel / blue-green schema swap.
- (D) Secrets in CI: OIDC to cloud / stored CI secrets / vault.
- (O) Manual gates: who approves a prod apply; change-window rules.

**Environment topology**

- (O) Per env (dev / test / prod): warehouse account or workspace, catalog /
  database, compute size, who has access, naming scheme, network mode.

---

## Not applicable is a valid answer

If an area does not apply, record *that* in the deliverable
("No reconciliation - single non-critical reference feed, monitored by freshness
only") rather than leaving the file empty.
