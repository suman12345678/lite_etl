# Pipeline blueprint - Northwind Commerce (DEMO)

> The runnable shape of the **data pipeline** (Dagster asset graph, runs on
> schedules / the S3 sensor, must publish by 06:00 UTC). The **deploy pipeline**
> (`terraform plan/apply` + `dbt build` on merge, dev -> stg -> prd) is in
> [`deployment-and-iac.md`](deployment-and-iac.md).

## Pipeline: `northwind_daily`  (sources: all 6, business date D, publish by 06:00 UTC)

```mermaid
flowchart TD
  subgraph ingest["ingest assets (per source, partitioned by D)"]
    P1[oltp_ingest\n4h cadence] --> BZ1[bronze.oltp__*]
    P2[shopify_ingest\nhourly] --> BZ2[bronze.shopify__*]
    P3[pos_ingest\nS3 sensor + 04:00 sweep] --> BZ3[bronze.pos__txn]
    P4[salesforce_ingest\n6h] --> BZ4[bronze.sfdc__*]
    P5[ga4_extract\n04:00 D-2 shard] --> BZ5[bronze.ga4__session]
    P6[fx_ingest\n05:00] --> BZ6[bronze.fx__rate]
  end
  BZ1 & BZ2 & BZ3 & BZ4 & BZ5 & BZ6 --> SF[dbt source freshness]
  SF --> DRIFT[schema-drift check vs sources.yml]
  DRIFT -->|drift| HALT[halt + ticket + page]
  DRIFT -->|ok| CB["curated_build\ndbt build --select staging+ intermediate+ marts+ --exclude tag:recon\n(run + generic/expectation tests + snapshots)"]
  CB -->|test fail| HALT
  CB --> RC{{reconcile  (Dagster asset check)\ndbt test --select tag:recon + python manifest compare}}
  RC -->|FAIL| BLOCK[no publish · exit non-zero · PagerDuty]
  RC -->|PASS| PUB[publish assets\ngold + gold_pii transaction per table group]
  PUB --> REG[catalog_register\nUC tags + comments + lineage + _SUCCESS]
  REG --> WM[advance _state.watermarks]
  WM --> MET[emit metrics + Elementary report]
```

## Task / asset table

| Asset | Depends on | Retry (transient) | On permanent failure | Idempotent? |
|-------|-----------|-------------------|----------------------|-------------|
| `<src>_ingest` (x6) | schedule / S3 sensor | 3 / expo (30s,2m,8m) | stop + page | yes (new `run_id`; POS supersede) |
| `dbt source freshness` | all ingests fresh for D | 0 | stop (error band) | yes |
| `schema drift check` | freshness | 0 | halt + ticket + page (policy = fail) | yes |
| `curated_build` (dbt) | drift ok | 1 (Spark executor loss only) | stop + page | yes (`merge` on `unique_key`; snapshots deterministic) |
| `reconcile` (asset check) | `curated_build` | 0 | **block publish** + page | yes (read-only) |
| `publish` (x table group) | `reconcile` PASS | 2 | stop + page | yes (re-publish = no-op merge) |
| `catalog_register` | `publish` | 2 | warn (retry async) | yes |
| `advance_watermarks` | `catalog_register` | 1 | manual | yes |
| `emit_metrics` | publish | 1 | warn | yes |

## Policies

- **Trigger:** `pos_ingest` = S3 event sensor (+ 04:00 sweep backstop); other
  ingests = cron; `curated_build` = asset dependency once D's ingest assets are
  fresh; manual = Dagster backfill.
- **Backfill:** `dagster job backfill --partition-range D0...D1` over the ingest
  assets, then `curated_build` over the same range; one `run_id` per business
  date, oldest first; each date's watermark advances only on its own reconcile
  PASS. Weekend window on the `prd` on-demand pool for the 24-month go-live load.
- **Concurrency:** max 1 `curated_build` per env at a time; ingest assets up to 4
  parallel; backfill capped at 3 concurrent dates.
- **The reconciliation gate:** `reconcile` is a **blocking asset check** - FAIL
  => `publish`/`catalog_register` never materialise, run exits non-zero, no
  `_SUCCESS`, watermark unchanged, PagerDuty fires with the `_reconciliation.json`
  link.
- **Alert points:** ingest failure; POS file missing past 04:30; schema drift;
  `dbt` test over threshold; reconcile FAIL; `curated_build` not done by 05:45
  (early warning); cost alarm at 80% of budget; SLA breach at 06:00.
- **SLA chain:** ingests done 05:00 -> `curated_build` 05:15-05:50 -> reconcile
  05:50-05:55 -> publish + register 05:55-06:00. 10 min of slack before the
  06:30 Looker refresh.
