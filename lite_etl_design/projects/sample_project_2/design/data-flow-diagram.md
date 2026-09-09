# Data-flow diagram - Northwind Commerce (DEMO)

> How data moves through the zones per source shape. Four shapes cover the six
> sources: incremental pull (OLTP, Shopify, Salesforce), file-arrival (POS),
> prior-day snapshot (GA4), reference carry-forward (FX).

## Shape A - incremental pull: `oltp` / `shopify` / `salesforce`

```mermaid
flowchart TD
  A[(Source)] -->|"extract WHERE updated_at > watermark - lookback\nrun_id assigned"| B[bronze.&lt;src&gt;__&lt;obj&gt;\nDelta, _run_id/_extracted_at/_ingest_date]
  B -->|"schema check vs sources.yml contract"| C{Schema drift?}
  C -->|yes| X[Halt + open ticket + page]
  C -->|no| D[silver: stg_&lt;src&gt;__&lt;entity&gt; (view)\nrename / cast / light cleanse]
  D --> E[silver: int_&lt;domain&gt;__* (ephemeral)\ndedupe, FX->USD, identity hash]
  E --> F{dbt tests}
  F -->|pass| G[gold marts\nsnapshot -> dim_*, merge -> fct_*]
  F -->|reject| Q[silver reject table\n+ reason_code]
  G --> H{reconcile asset check}
  H -->|PASS| I[publish -> gold / gold_pii + UC register]
  H -->|FAIL| X
  I -->|advance watermark| J[(_state.watermarks Delta)]
```

## Shape B - file-arrival: `pos`

```mermaid
flowchart TD
  A[/S3: pos/dt=D/store=s/txns.csv.gz (+ totals.csv)/] -->|"S3 event -> Dagster sensor\n(4:00 sweep as backstop)"| B[extract: gunzip + parse\ncents/100, txn_ts+store_tz -> UTC, run_id]
  B --> C[bronze.pos__txn\npartition _ingest_date, _file_etag]
  C --> D{superseding file_etag for (dt,store)?}
  D -->|yes| E[mark prior rows _superseded=true (keep)]
  D -->|no| F[proceed]
  E --> G[silver: stg_pos__txn keeps latest non-superseded etag per (dt,store)]
  F --> G
  G --> H[int_sales__order_store -> gold.fct_order (channel=store) + fct_order_line]
  H --> I{dbt tests + reconcile vs totals.csv per store}
  I -->|PASS| J[publish]
  I -->|FAIL| X[Halt + page]
```

## Shape C - prior-day snapshot: `ga4`

```mermaid
flowchart TD
  A[(BigQuery analytics_*.events_YYYYMMDD)] -->|"04:00 UTC job on D-2 shard\naggregate events -> session grain"| B[Parquet -> s3 inbound/ga4/dt=D-2]
  B --> C[bronze.ga4__session (full replace of that session_date)]
  C --> D[silver: stg_ga4__session -> int_web__session\njoin hashed email on 'login' events -> customer_sk or -1]
  D --> E{dbt tests}
  E -->|pass| F[gold.fct_web_session (append, idempotent per session_date)]
  E -->|reject| Q[drop 0-event sessions]
  F --> G{reconcile: dupes on (session_id, session_date)}
  G -->|PASS| H[publish]
  G -->|FAIL| X[Halt]
```

## Shape D - reference carry-forward: `fx_rates`

```mermaid
flowchart TD
  A([open.er-api.com/v6/latest/USD]) -->|"05:00 UTC GET, retry on 503"| B[bronze.fx__rate (rate_date, currency, rate)]
  B --> C{rate present for currency/date?}
  C -->|no / weekend| D[carry forward last known, is_carried_forward=true]
  C -->|yes| E[use as-is]
  D --> F[gold.dim_fx_rate (merge on rate_date+currency)]
  E --> F
  F --> G[consumed by silver int_*__* currency conversion]
```

## Zone contract

| Zone | Contents | Mutability | Retention |
|------|----------|-----------|-----------|
| S3 inbound | raw files as delivered | immutable; superseding files get a new key | purge after 60 days |
| bronze | exact source rows as landed, `_run_id` tagged; POS `_superseded` flag | append-only; new `run_id` per replay | 60 days then `VACUUM` |
| silver reject | rows failing DQ + `reason_code` | append | 90 days |
| silver (staging/intermediate) | transformed, DQ-passed, pre-publish | rebuilt per run (views/ephemeral) | n/a |
| gold / gold_pii | consumer-facing dims + facts + aggs | per load pattern (SCD2 / merge / append) | gold 5y; gold_pii 25m |

## Checkpoints

- **Schema-drift check:** after landing, before `silver` - policy **fail**
  (source contract in `sources.yml` + per-file JSON schema). Because `01`/`06`.
- **DQ checkpoint:** inside `dbt build` - routes rows pass / reject; fails the
  run at >0.5% quarantine or any error test. Because `04`.
- **Reconciliation checkpoint:** after `gold` build, before publish - blocking
  Dagster asset check; a FAIL blocks publish and pages. Because `05`.
- **PII-leak check:** singular dbt test asserting no raw email/phone/name in any
  `gold.*` object. Because `08`.
