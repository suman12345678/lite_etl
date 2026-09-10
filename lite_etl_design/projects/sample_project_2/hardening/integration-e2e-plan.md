# Integration & end-to-end plan - Northwind Commerce (DEMO)

> Phase 5 deliverable. The scenarios that test real components together and the
> whole Dagster graph through a business date.

- **Dev env used:** `northwind_dev` catalog, dev S3 buckets, Dagster deployment
  `northwind-dev` (`pipeline/environments-and-config.md`)
- **Isolation:** each run creates schema `ci_int_<run_id>` / `e2e_<date>` in
  `northwind_dev`, and an S3 prefix `s3://northwind-dev-inbound/_test/<run_id>/`;
  both dropped in a `finally` even on failure
- **Auth:** OIDC -> `northwind-dev-ci`; Databricks token from the dev GitHub
  Environment secret; no personal tokens

## Integration scenarios  (2-3 real components, real dev warehouse + storage)

| # | Components | Scenario | Asserts | Traces to |
|---|-----------|----------|---------|-----------|
| I1 | `extractor` + `landing` | extract `oltp` `sample` window -> land to `bronze` | rows in `bronze.oltp__*`, `manifest.json` in `_manifests/`, `_run_id` / `_source_file` / `_extracted_at` set, high-watermark returned but **not** committed | `component-design.md` extractor; `02` |
| I2 | `landing` + dbt staging | land `shopify` `sample`, then `dbt build --select staging.shopify+ --target dev` | staging rows == `golden/`; `test=true` order filtered (DQ09); CAD order retains `presentment_currency` | `transformation-design.md`; DQ09 |
| I3 | dbt marts + `reconciliation` | build `gold` for the golden date, then `dbt test --select tag:recon` + `recon.compare` | recon **PASS**; `_reconciliation.json` has all 8 checks with `expected`/`actual`/`delta`/`verdict` | `05`; `reconciliation-fixtures.md` |
| I4 | `reconciliation` + `publisher` | run with `r2_web_fail_high` fixture | `recon` verdict FAIL; `publish` **not** called; process exit non-zero; alert stub captured with the `_recon` link; watermark unchanged | `05` gate; `pipeline-blueprint.md` |
| I5 | `secrets` resolver + `extractor` | `secret-scope://northwind/dev/oltp#password` missing | fails fast, clear message, **no** partial `bronze` write, no manifest | `component-design.md` secrets; `08` |
| I6 | `publisher` + `catalog_register` + `state` | publish a PASS date, then re-publish the same date | second publish is a no-op merge; one `_SUCCESS`; `catalog_register` idempotent; watermark advances once | `component-design.md` publisher; replay assertion |
| I7 | `pos` S3 sensor + `extractor` + `landing` | drop `pos/dt=.../store=001/txns.csv.gz` then a `txns_v2` with a new etag | sensor fires one run per `(store, D)`; v2 lands, v1 rows marked `_superseded=true`; row-count identity (R1) still balances | `01` POS quirks; `pos_s3_sensor` |

## Contract tests

| # | Contract | Scenario | Asserts | Traces to |
|---|----------|----------|---------|-----------|
| C1 | source schema (`sources.yml`) | apply each `<src>/schema_drift.*` fixture (added / removed / retyped / reordered column) | the schema-drift check **halts** the run + opens a ticket + pages (policy = fail); `curated_build` does not start | DQ15; `pipeline-blueprint.md`; `/validate-config` #15 |
| C2 | `gold` output schema | snapshot `gold.*` + `gold_pii.*` column names + types to `tests/contracts/gold_schema.json`; diff on PR | a removed/retyped `gold` column **fails CI** until the PR carries a `contract-change` label + a consumer-notice link | `06`; consumer exposures |
| C3 | consumer exposures | `dbt ls --select exposure:looker_sales exposure:braze_segments exposure:finance_close` | all resolve; their upstream `gold` models exist | `transformation-design.md` s.9; `00` out-of-scope consumers |
| C4 | `_reconciliation.json` schema | validate a produced report against `tests/contracts/recon_report.schema.json` | matches the `CheckResult` / `ReconResult` shape; Elementary ingest does not break | `recon/gate.py`; `05` |

## End-to-end scenarios  (whole pipeline, real Dagster run in dev)

| # | Scenario | Setup | Asserts | Traces to |
|---|----------|-------|---------|-----------|
| E1 | happy golden day | full synthetic day for all 6 sources | `gold` == `golden/`; recon PASS; `publish` + `catalog_register` done; `_SUCCESS` written; watermarks advanced; run finished before the simulated 06:00 SLA marker | `pipeline-blueprint.md`; `09` SLA |
| E2 | one source late | hold the `pos` files past 04:30 | `pos_ingest` retries then the run **waits**; early-warning alert at the 05:45 marker; **no partial publish**; when files arrive, the sweep + `curated_build` complete | `07` catch-up; DQ14 |
| E3 | DQ over fail threshold | inject `> 0.5%` bad `fct_order` rows in `oltp` (`bad_rows`) | `curated_build` **fails**; nothing publishes; `reject__fct_order` populated with `reason_code`; page fired | DQ03; `04` thresholds |
| E4 | reconciliation break | `store` GMV `-0.9%` vs POS totals (`r2_store_fail_low`) | `reconcile` FAIL; `publish` not materialised; run non-zero; `_reconciliation.json` names `store` + `store_id`; PagerDuty page | `05`; `reconciliation-fixtures.md` R2 |
| E5 | re-run same day | run E1 twice | identical `gold`; no double count; watermark advances once; one `_SUCCESS`; `_reconciliation.json` body identical modulo `run_id`/ts | replay assertion |
| E6 | backfill window | `dagster job backfill --partition-range D-3...D-1` over ingest then `curated_build` | 3 dates run **oldest first**, `<= 3` concurrent; each reconciles independently; each watermark advances only on its own PASS; final `_state.watermarks` == `D-1` | `07` backfill; `backfill.py` |
| E7 | rollback | publish a deliberately bad day with the gate bypassed (`recon.gate` test hook), then run the `runbook.md` "bad publish already consumed" steps | `RESTORE gold.<t> TO VERSION AS OF <n>` restores rows; the business date rebuilds clean; runbook steps are accurate; timing recorded | `runbook.md`; `deployment-and-iac.md` s.6 |
| E8 | Black-Friday load | 5x-volume golden day on the `prd`-sized job cluster in dev | `curated_build` < **35 min**; each ingest < **20 min**; recon PASS; spend within the run's share of budget; photon on `curated_build` observed | `09` peak load + runtime budget |

## Stubbed vs real

| Dependency | Unit / data | Integration | E2E |
|------------|-------------|-------------|-----|
| source APIs / Postgres / BigQuery | mock (`respx`), DuckDB | committed fixtures loaded to a test schema | recorded full-day synthetic set |
| Databricks warehouse | DuckDB (`--target ci`) | real (dev) | real (dev, isolated schema) |
| object storage (S3) | local files | real (dev bucket, `_test/` prefix) | real (dev bucket) |
| Dagster orchestrator | direct Python calls | direct asset fn calls | **real** `dagster job execute` |
| secrets (Secrets Manager / scopes) | fake resolver | real dev secret scope (**TODO** F2: scopes not yet in IaC) | real dev secret scope |
| PagerDuty / Slack | captured stub | captured stub | captured stub (assert payload, do not page) |
| GA4 BigQuery aggregation | fixture Parquet | fixture Parquet | fixture Parquet (real BQ extract is a manual pre-go-live check, O3) |

## Runtime budget

| Suite | Budget | Where |
|-------|--------|-------|
| unit + data (DuckDB) | < 5 min | PR - blocking |
| contract (C1-C4) | < 3 min | PR - blocking |
| integration fast subset (I1, I4, I5) | < 12 min | PR - blocking |
| integration full (I1-I7) | < 30 min | nightly on `main` |
| E2E E1, E3, E4, E5 | < 45 min | nightly on `main` + **pre-promote** |
| E2E E2, E6, E7, E8 | < 90 min | nightly only (E8 needs the big cluster) |

A PR-blocking suite over budget for 3 consecutive runs -> move it to nightly and
open a perf ticket (do not silently extend the budget).
