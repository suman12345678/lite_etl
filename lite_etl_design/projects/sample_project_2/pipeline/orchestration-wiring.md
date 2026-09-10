# Orchestration wiring - Northwind Commerce (DEMO)

> Phase 4 deliverable. How the Phase 3 components become the runnable
> `northwind_daily` pipeline on Dagster. The DAG shape is fixed by
> `design/pipeline-blueprint.md`; this file is the wiring detail.

- **Orchestrator:** **Dagster** (Cloud hybrid; ECS Fargate agent) - `07`, ADR-005.
  Fallback `oss_selfhost` = Dagster OSS webserver + daemon on the same ECS
  cluster, identical asset code (Q3 / `orchestrator/` module `var.mode`).
- **Deployment:** a **code location** built from `dagster/`, deployed by
  `main.yml` / `promote.yml` per env (`dagster-cloud` CLI for `cloud_agent`,
  image push + service update for `oss_selfhost`). One Dagster deployment name
  per env (`northwind-dev` / `-stg` / `-prd`).
- **Repo path:** `northwind_dagster/` (the design calls it "the `dagster/` code
  location"; the package is named `northwind_dagster` so it never shadows the
  installed `dagster` library on the import path).
- **Partitions:** one daily partition per business date `D`, UTC
  (`partitions.py`). Every asset below is partitioned by `D`.

## Pipeline: `northwind_daily`  (all 6 sources, business date D, publish by 06:00 UTC)

| # | Design asset | Component / call | Dagster unit | Config / notes |
|---|--------------|------------------|--------------|----------------|
| 1 | `oltp_ingest` | `extractors.oltp.run(date=D)` | asset `oltp_ingest` (group `ingest`) | cron `0 */4 * * *`; retry 3 / expo 30s,2m,8m |
| 2 | `shopify_ingest` | `extractors.shopify.run` | asset `shopify_ingest` | cron `0 * * * *`; 24h lookback; retry 3 / expo |
| 3 | `pos_ingest` | `extractors.pos.run` | asset `pos_ingest` | **S3 sensor** + `0 4 * * *` sweep; per `(store, D)`; supersede on new etag; retry 3 / expo |
| 4 | `salesforce_ingest` | `extractors.salesforce.run` | asset `salesforce_ingest` | cron `0 */6 * * *`; retry 3 / expo |
| 5 | `ga4_extract` | `extractors.ga4.run` (D-2 shard) | asset `ga4_ingest` | cron `0 4 * * *`; skip+retry next cycle if shard not final (48h budget); retry 3 / expo |
| 6 | `fx_ingest` | `extractors.fx.run` | asset `fx_ingest` | cron `0 5 * * *`; carry-forward on miss; retry 3 / expo |
| 7 | `land raw` (x6) | `extractors.common.landing.write` | inside each ingest asset | new `run_id` per write; manifest to `_manifests/` |
| 8 | `dbt source freshness` | `extractors.common.dbt_runner` -> `dbt source freshness` | asset `source_freshness` | deps: assets 1-6 fresh for D; retry 0; error band => stop |
| 9 | `schema-drift check` | `dbt` contract check vs `sources.yml` | asset `schema_drift` | deps: `source_freshness`; policy = **fail** -> halt + ticket + page; retry 0 |
| 10 | `curated_build` | `dbt_runner.run_build(select="staging+ intermediate+ marts+ --exclude tag:recon", target=<env>, vars={business_date,run_id})` | `@dbt_assets` block `curated_build` | deps: `schema_drift` ok; retry **1** (Spark executor loss only); concurrency max 1 / env |
| 11 | `reconcile` | `recon.gate.run_gate(D, run_id, target, settings)` = `dbt test --select tag:recon` + `recon.compare` manifest compare | **blocking asset check** `reconcile` on the `curated_build` gold assets | retry **0**; FAIL => downstream never materialises, run exits non-zero, PagerDuty |
| 12 | `publish` (x table group) | `publish.publish.run(D, run_id, target)` | asset `publish` | deps: `reconcile` PASS; retry 2; txn per table group per D; re-publish = no-op merge |
| 13 | `catalog_register` | `publish.catalog.register(...)` | asset `catalog_register` | deps: `publish`; retry 2; warn + async retry on fail; writes `_SUCCESS` |
| 14 | `advance_watermarks` | `extractors.common.state.advance(...)` | asset `advance_watermarks` | deps: `catalog_register`; retry 1; manual on fail |
| 15 | `emit_metrics` | `obs.metrics.emit(...)` + Elementary report | asset `emit_metrics` | deps: `publish`; retry 1; warn on fail |
| 16 | `lineage.emit` | `lineage.emit.run(...)` | asset sensor / hook on `catalog_register` | OpenLineage events; retry async |

### Dependency edges (from `pipeline-blueprint.md`)

```
oltp_ingest  shopify_ingest  pos_ingest  salesforce_ingest  ga4_ingest  fx_ingest
        \        \         \       |        /        /
                       source_freshness
                              |
                        schema_drift
                              |
                        curated_build  ──(dbt gold assets)──►  [check: reconcile]  ◄blocking
                              |                                        │ PASS
                              └────────────────────────────────────────┤
                                                                       ▼
                                                                    publish
                                                                       │
                                                                catalog_register
                                                              /        │        \
                                                    advance_watermarks │       emit_metrics
                                                                       ▼
                                                                lineage.emit
```

## Triggers

- **Schedules (`schedules.py`):** one `ScheduleDefinition` per ingest cron above,
  all `execution_timezone="UTC"`; plus `curated_build_schedule` at `15 5 * * *`
  that requests `curated_build`+downstream for `D = today` once the ingest assets
  report fresh (guarded by an `AutoMaterializePolicy` / freshness check).
- **Sensors (`sensors.py`):** `pos_s3_sensor` on `s3://northwind-<env>-inbound/pos/`
  object-created events -> request `pos_ingest` for the parsed `(store, D)`.
  `04:00` sweep schedule is the backstop.
- **Dependencies:** none upstream of `northwind_daily` - it is the top pipeline.
  `fx_ingest` must be fresh for D before `curated_build` (edge above).
- **Databricks Workflows** (outside Dagster) still runs the nightly
  `OPTIMIZE`/`VACUUM` maintenance job - ADR-005.

## Cross-cutting

- **Retry policy:** transient (API 429/5xx, S3 throttle, executor loss) =
  `RetryPolicy(max_retries=3, delay=30, backoff=EXPONENTIAL)` on ingests
  (`max_retries=1` on `curated_build`); permanent (auth fail, schema drift =
  fail, DQ over threshold, reconcile FAIL) = **no retry**, stop, page. - `07`
- **The reconciliation gate:** `reconcile` is a `@asset_check(blocking=True)` on
  the `curated_build` gold assets. On `AssetCheckResult(passed=False)`:
  `publish` / `catalog_register` never materialise, the run exits non-zero, no
  `_SUCCESS` object is written, `_state.watermarks` is unchanged, and PagerDuty
  fires with the `_reconciliation.json` S3 link. `recon/gate.py::run_gate`
  already returns `ReconResult(verdict=...)`; the check maps `verdict != "PASS"`
  to `passed=False`. - `05`, ADR-005
- **Backfill entrypoint (`backfill.py`):**
  `dagster job backfill --partition-range D0...D1` over the `ingest` group, then
  `curated_build`+downstream over the same range. One `run_id` per business date,
  **oldest first**; each date's watermark advances only on its own `reconcile`
  PASS. Go-live 12/24-month load runs on the `prd` on-demand pool over a weekend
  window (Q2 - depth is a runtime parameter, not a code change). - `07`,
  `pipeline-blueprint.md`
- **Concurrency:** `max 1` `curated_build` per env (Dagster concurrency key
  `curated_build/<env>`); ingest assets up to `4` parallel; backfill capped at
  `3` concurrent dates.
- **Alert routing (`resources.py` alert resource):** PagerDuty (page) for SLA
  breach / reconcile FAIL / permanent error; `#northwind-data` Slack for
  warnings, DQ digests, backfill progress. Analytics Eng on-call primary; Data
  Platform on-call secondary for agent/infra. - `07`
- **SLA markers:** early-warning alert if `curated_build` not done by 05:45 UTC;
  SLA breach alert at 06:00 UTC if `_SUCCESS` absent. 10 min slack before the
  06:30 Looker refresh.

## Skeleton files to scaffold (in `build/repo/northwind_dagster/`)

```
northwind_dagster/
  definitions.py        # Definitions(assets=[...], asset_checks=[reconcile], schedules, sensors, resources)
  partitions.py         # DailyPartitionsDefinition(start_date=..., timezone="UTC")  # TODO start_date
  resources.py          # databricks / s3 / secrets / dbt / pagerduty / slack resources - refs + TODO
  assets/
    __init__.py
    ingest.py           # 6 @asset ingest fns, group="ingest", RetryPolicy(3, expo); calls extractors.<src>.run
    transform.py        # @dbt_assets(manifest=...) curated_build; RetryPolicy(1); concurrency key
    publish.py          # publish, catalog_register, advance_watermarks, emit_metrics @asset fns
  checks/
    __init__.py
    reconcile.py        # @asset_check(asset=<gold>, blocking=True) -> maps recon.gate.run_gate verdict
  schedules.py          # ScheduleDefinition per cron above + curated_build_schedule
  sensors.py            # pos_s3_sensor (S3 object-created) + 04:00 sweep backstop note
  backfill.py           # thin CLI wrapper documenting the --partition-range entrypoint
  deployment.yaml       # code-location descriptor; var mode cloud_agent | oss_selfhost
```

Stubs only: correct structure, asset names, dependency edges, retry config, the
blocking check. `TODO` for the partition start date, resource endpoints, the
PagerDuty routing key, and the Elementary report call.
