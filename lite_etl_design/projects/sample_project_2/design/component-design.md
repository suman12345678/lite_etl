# Component design - Northwind Commerce (DEMO)

> Per-component responsibility / interfaces / config / failure modes /
> idempotency for the risk-carrying components. dbt-owned transform + DQ are one
> component here (ELT-on-warehouse); details in
> [`transformation-design.md`](transformation-design.md).

### `extractor` (per source: oltp / shopify / salesforce / pos / ga4 / fx)

- **Responsibility:** pull one source for one business date/window and land raw
  rows + a `manifest.json` in `bronze`. Does not transform (POS parse, Shopify
  flatten, GA4 aggregate are the only exceptions).
- **Triggered by:** Dagster schedule (cron) or the S3 sensor (`pos`).
- **Inputs:** source connection (secret scope ref), stored watermark from
  `_state.watermarks`, config (`objects`, `lookback`, `page_size`).
- **Outputs:** `bronze.<src>__<obj>` Delta rows tagged `_run_id`,
  `_source_file`, `_extracted_at`, `_ingest_date`; `manifest.json` (window, row
  counts, checksums) to `s3://…-lakehouse/_manifests/`.
- **Configuration:** `extractors/config/<src>.yml`; per-env overrides via
  `--target`; secret refs `secret-scope://northwind/<env>/<src>#<field>`.
- **Key logic:** resolve watermark - build request/query (`updated_at >
  wm - lookback`) - page/stream to Parquet - `COPY INTO` / Delta append -
  write manifest - hand back new high-watermark (not yet committed).
- **Failure modes:**

  | Failure | Detection | Response |
  |---------|-----------|----------|
  | API 429 / 5xx, replica unavailable | HTTP status / driver error | retry 3x expo (30s/2m/8m), then stop + page |
  | Partial page set | manifest row count vs `Link`/job total | fail run, no bronze commit |
  | Schema drift vs `sources.yml` | contract check post-land | halt, ticket, page (policy = fail) |
  | POS file re-sent | new `_file_etag` for `(dt, store)` | land, mark prior `_superseded=true` |
  | GA4 shard not final | job returns < expected rows | skip, retry next cycle (48h budget) |

- **Idempotency:** a re-run writes a **new** `run_id` folder; loader/silver keep
  only the latest non-superseded rows per business date. Watermark advances only
  after reconcile PASS.
- **Scaling knobs:** page size, JDBC fetch size, Bulk API batch, extractor
  parallelism per source.

### `dbt runner` (transform + data quality)

- **Responsibility:** `dbt build` the selected models - staging (view) ->
  intermediate (ephemeral) -> marts (table / incremental merge) + snapshots +
  seeds + **all DQ tests**. One component; DQ is not separate.
- **Triggered by:** Dagster `dagster-dbt` assets once the business date's ingest
  assets are fresh; also CI.
- **Inputs:** `bronze.*`, seeds, `_state`, `--vars {business_date, run_id}`,
  `--target <env>`, prod `manifest.json` for `--defer` in CI.
- **Outputs:** `silver.*`, `gold.*`, `gold_pii.*`, `run_results.json`,
  `manifest.json`, Elementary tables, `silver` reject tables.
- **Configuration:** `dbt_project.yml`, `_models.yml` per folder, `profiles.yml`
  (CI-injected), `packages.yml`.
- **Key logic:** `dbt build --select <pipeline selector>+ --vars ...` - run +
  test + snapshot in DAG order; a failing error-severity test aborts the build
  and its downstream.
- **Failure modes:**

  | Failure | Detection | Response |
  |---------|-----------|----------|
  | error-severity test fails | `dbt build` non-zero | abort build, no publish, page |
  | quarantine > 0.5% batch | singular test on reject count | fail run |
  | transient Spark executor loss | task error | Dagster retry once, then stop |
  | snapshot gap (missed day) | `dbt_valid_to` continuity test | backfill that date before proceeding |

- **Idempotency:** incremental `merge` on `unique_key` replaces exactly the
  business date's rows; snapshots deterministic on `updated_at`; `agg_*`
  full-rebuilt.
- **Scaling knobs:** job cluster size, `threads`, photon on `curated_build`,
  incremental lookback window.

### `reconciliation engine`

- **Responsibility:** run the `05` checks against the freshly built `gold` and
  the source control totals; write `_reconciliation.json`; decide PASS/FAIL.
- **Triggered by:** Dagster `reconcile` **asset check** after the `gold` assets,
  before `publish`.
- **Inputs:** `gold.*`, source control totals (Shopify payout export, POS
  `totals.csv`, SFDC closed-won), `bronze` manifests, 28-day baseline table.
- **Outputs:** `_reconciliation.json` (per check: expected, actual, delta,
  tolerance, verdict) to `s3://…-lakehouse/_recon/dt=.../`; asset-check result;
  Elementary row.
- **Key logic:** row-count identity per source - per-channel GMV vs control
  total (±0.5%) - refund balancing + linkage - order = sum(lines) - FX coverage
  - duplicate keys - distribution drift vs baseline - PII-leak scan. Any hard
  FAIL => asset check fails.
- **Failure modes:**

  | Failure | Detection | Response |
  |---------|-----------|----------|
  | GMV delta > 0.5% | control-total check | **block publish**, page, `_recon` report shows the channel |
  | orphan refund | linkage check | block publish |
  | drift > 60% | baseline check | block publish (warn at 30%) |
  | control total file missing | pre-check | block publish, page source owner |

- **Idempotency:** pure read + report; safe to re-run. No auto-retry of
  reconciliation itself.

### `publisher`

- **Responsibility:** make the reconciled business date live in `gold` /
  `gold_pii` and register/refresh it in Unity Catalog.
- **Triggered by:** Dagster `publish` asset, only if `reconcile` asset check
  passed.
- **Key logic:** one transaction per table group per business date; set table
  properties/comments from `_models.yml`; refresh UC tags; emit lineage +
  `_SUCCESS`; advance the source watermarks in `_state.watermarks`.
- **Failure modes:** transaction failure -> nothing commits, watermark
  unchanged, retry x2 then page.
- **Idempotency:** re-publishing the same business date is a no-op merge.

### `orchestrator` (Dagster)

- **Responsibility:** the asset graph (ingest -> dbt assets -> reconcile check ->
  publish -> catalog register), schedules, the S3 sensor, retries, backfills,
  alert routing.
- **Config:** `dagster/` code location; `deployment.yaml`; resources for
  Databricks, S3, secrets; per-env via Dagster deployments.
- **Failure modes:** agent down -> Platform on-call paged (infra), runs queue;
  schedule tick missed -> next tick + backfill; asset check FAIL -> downstream
  not materialised.
- **Idempotency:** partitioned assets keyed by business date; re-materialising a
  partition is safe.

### `secrets & security`

- **Responsibility:** resolve `secret-scope://` refs at runtime; hold the
  per-subject hashing salt; enforce the PII split; apply UC row filter + column
  mask on `gold_pii`; KMS at rest.
- **Key logic:** extractors + dbt read secret scopes (never values in code);
  `silver` hashes email/phone with salt from `northwind/<env>/pii#salt`;
  `gold_pii` models write real values; Terraform attaches the UC row filter
  (marketable-consent) + column mask + `northwind_pii_readers` grant.
- **Failure modes:** secret missing -> fail fast; salt rotation only for RTBF
  crypto-shred; leak-check test failure blocks publish.

### `observability`

- **Responsibility:** metrics, DQ dashboard, cost + freshness alarms, paging.
- **Outputs:** Dagster asset health; Elementary DQ dashboard; Databricks SQL
  cost/freshness dashboard; CloudWatch alarms -> SNS -> PagerDuty/Slack.
- **Healthy definition:** all ingest assets fresh for the business date,
  `curated_build` green, reconcile PASS, published < 06:00 UTC, spend < 80% of
  budget.

### `IaC / provisioning` (Terraform) - see [`deployment-and-iac.md`](deployment-and-iac.md)

- **Responsibility:** provision UC catalogs/schemas/grants + `gold_pii`
  governance, storage + KMS + external locations, the Dagster ECS agent, the GA4
  GCP service account, CI OIDC roles, CloudWatch alarms. Not Delta objects, not
  secret values, not Dagster code.
- **Idempotency:** `terraform plan/apply`; drift detected nightly.

### `CI/CD deploy` (GitHub Actions) - see [`deployment-and-iac.md`](deployment-and-iac.md)

- **Responsibility:** PR checks (lint / validate / slim `dbt build` /
  `terraform plan`); on merge apply + build + Dagster deploy for dev; manual
  promotion dev -> stg -> prd with the same SHA + dbt manifest.
- **Failure modes:** plan shows unexpected destroy -> block; dbt tests red ->
  block merge; prod apply outside change window -> block unless `hotfix`.

### `state store`

- **Responsibility:** source watermarks (`_state.watermarks` Delta) + Dagster
  run/partition status.
- **Idempotency / durability:** Delta history = backup; weekly deep clone to
  `eu-west-2`.
