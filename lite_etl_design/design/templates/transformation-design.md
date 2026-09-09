# Transformation design (dbt project blueprint)

> Phase 2 deliverable. How the transformation layer is built - assumed to be dbt
> unless `10-platform-and-deployment.md` says otherwise. Every choice carries a
> "because <requirement>". If the project is not dbt, keep the same headings and
> describe the equivalent (SQLMesh models, Spark jobs, SQL scripts).

- **Project:**
- **Framework & version:** dbt Core `x.y` / dbt Cloud / SQLMesh / ...
- **Adapter(s):** `dbt-<engine>` - because `10` target engine(s)
- **Engine portability stance:** single adapter / kept swappable / multi-engine -
  because `10`. Vendor-specific SQL is confined to `<macros / this layer>`.

## 1. Project layout

```
<repo>/
  dbt_project.yml
  profiles.yml            # or env / CI-injected
  packages.yml            # dbt_utils, dbt_expectations, elementary, ...
  models/
    staging/       <src>/  stg_<src>__<entity>.sql   + _<src>__sources.yml + _<src>__models.yml
    intermediate/  int_<domain>__<step>.sql
    marts/         <domain>/  dim_<x>.sql  fct_<y>.sql  + _<domain>__models.yml
  snapshots/       <entity>_snapshot.sql
  seeds/           <reference>.csv
  macros/          <project macros>
  tests/           <singular tests>.sql
  analyses/
```

- **One project or project-per-domain:** _choice_ - because `10`
- **Mono-repo vs dedicated transform repo:** _choice_

## 2. Layer model

| Layer | Name convention | Contents | Materialisation | Grain |
|-------|-----------------|----------|-----------------|-------|
| Staging | `stg_<src>__<entity>` | 1:1 with a landed source object; rename, cast, light cleanse only | view / ephemeral | source row |
| Intermediate | `int_<domain>__<step>` | joins, dedupe, business logic building blocks | ephemeral / view | varies |
| Marts | `dim_*` / `fct_*` (or `gold_*`) | consumer-facing dimensions & facts | table / incremental | stated per table |

Map this to raw/bronze -> cleansed/silver -> curated/gold as the requirements name it.

## 3. Sources & freshness

| Source (`sources.yml`) | Landed dataset | `loaded_at_field` | warn_after | error_after |
|------------------------|----------------|-------------------|-----------|-------------|
| `<src>.<entity>` | | | | |

- `dbt source freshness` runs: _when_ - because `01` cadence / `07` SLA.

## 4. Materialisation & incremental strategy

| Model / group | Materialisation | Incremental strategy | `unique_key` | Partition / cluster | Because |
|---------------|-----------------|----------------------|--------------|---------------------|---------|
| `fct_<y>` | incremental | `merge` / `insert_overwrite` / `append` | | | `02` load pattern, `09` volume |

- **Full-refresh policy:** when a `--full-refresh` is allowed / required.
- **Late-arriving data:** lookback window on the incremental filter.

## 5. History / SCD2

| Entity | Mechanism | Tracked columns | Strategy (`timestamp` / `check`) | Because |
|--------|-----------|-----------------|----------------------------------|---------|
| `dim_<x>` | dbt snapshot | | | `03` historisation |

## 6. Data quality as tests

| Check type | How | Runs in | Fails the build? |
|------------|-----|---------|------------------|
| Generic (`not_null`, `unique`, `accepted_values`, `relationships`) | `_models.yml` | every run + CI | yes |
| Expectations (ranges, regex, row counts, distribution) | `dbt_expectations` | every run | yes above threshold |
| Freshness | `dbt source freshness` | pre-run | yes |
| Anomaly / volume | `elementary` | every run | warn -> alert |
| Singular (bespoke SQL) | `tests/` | every run | yes |

- Maps to `04-data-quality.md` rules - reference each rule's row here.
- **Severity & thresholds:** `severity: warn|error`, `error_if`, `warn_if` per rule.

## 7. Reconciliation hooks

- Reconciliation checks from `05` implemented as: singular tests / an
  `on-run-end` audit / a separate step - state which, and that a FAIL blocks
  publish (exit non-zero, no downstream `dbt run`).
- `audit_helper` / `dbt_utils.equality` for source-to-target parity where used.

## 8. Packages, macros, seeds

| Package | Used for |
|---------|----------|
| `dbt_utils` | |
| `dbt_expectations` | |
| `elementary` | DQ reporting / anomaly detection |
| `codegen` / `audit_helper` | dev-only |

- **Project macros:** surrogate keys (`dbt_utils.generate_surrogate_key`),
  currency conversion, env-aware schema/database naming, cross-engine shims.
- **Seeds:** `<reference>.csv` - refresh owner and cadence.

## 9. Docs, exposures, lineage

- `dbt docs generate` published to: _where_ - because `06` catalog.
- Exposures declared for: _BI dashboards / regulatory extract / reverse-ETL_ -
  because `00` consumers / `06`.
- dbt lineage exported to the catalog (`manifest.json` / OpenLineage / Elementary)
  - because `06` lineage granularity.

## 10. Run interface

- **Per-pipeline invocation:** `dbt build --select <selector> --target <env>`
  (build = run + test + snapshot + seed).
- **Selectors** per pipeline / per source - list them.
- **State / slim CI:** `--defer --state <path> --select state:modified+` - because
  `10` slim-CI requirement.
- **Where it runs:** orchestrator task (`07`) / dbt Cloud job / CI - state which.

## 11. Open questions

| Q# | Impact on the transformation layer |
|----|------------------------------------|
| | |
