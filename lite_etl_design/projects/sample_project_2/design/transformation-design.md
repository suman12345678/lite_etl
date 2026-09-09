# Transformation design (dbt project blueprint) - Northwind Commerce (DEMO)

> Phase 2 deliverable. Every choice carries a "because <requirement>".

- **Project:** `northwind` (dir `dbt/` in the `northwind-data` mono-repo)
- **Framework & version:** dbt Core 1.8 - because `10` (not dbt Cloud; runs in
  Dagster via `dagster-dbt` and in CI)
- **Adapter(s):** `dbt-databricks` 1.8.x (runtime); `dbt-duckdb` for local +
  unit tests - because `10` target engine + portability
- **Engine portability stance:** single adapter, kept swappable. Vendor-specific
  SQL is confined to `macros/` (`optimize_table`, `current_ts`, `qualify_dedupe`,
  `surrogate_key`) and model `config()` blocks (incremental strategy) - because
  `10`.

## 1. Project layout

```
dbt/
  dbt_project.yml
  packages.yml            # dbt_utils, dbt_expectations, elementary, dbt_date, codegen
  profiles/               # profiles.yml templated per target, secrets injected by Dagster/CI
  models/
    staging/
      oltp/        stg_oltp__customers.sql  stg_oltp__products.sql  stg_oltp__orders.sql  stg_oltp__order_lines.sql
                   _oltp__sources.yml  _oltp__models.yml
      shopify/     stg_shopify__orders.sql  stg_shopify__refunds.sql  stg_shopify__fulfillments.sql  _shopify__*.yml
      pos/         stg_pos__txn.sql  stg_pos__txn_line.sql  _pos__*.yml
      salesforce/  stg_sfdc__account.sql  stg_sfdc__contact.sql  stg_sfdc__opportunity.sql  _sfdc__*.yml
      ga4/         stg_ga4__session.sql  _ga4__*.yml
      fx/          stg_fx__rate.sql  _fx__*.yml
    intermediate/
      customer/    int_customer__resolved.sql  int_customer__pii.sql
      sales/       int_sales__order_web.sql  int_sales__order_store.sql  int_sales__order_wholesale.sql
                   int_sales__order_unioned.sql  int_sales__lines.sql  int_sales__refunds.sql
      fx/          int_fx__daily.sql
      web/         int_web__session.sql
    marts/
      core/        dim_customer.sql  dim_product.sql  dim_store.sql  dim_account.sql  dim_fx_rate.sql  dim_date.sql
      sales/       fct_order.sql  fct_order_line.sql  fct_refund.sql  agg_sales_daily.sql  agg_customer_monthly.sql
      web/         fct_web_session.sql
      wholesale/   fct_wholesale_opportunity.sql
      pii/         dim_customer_pii.sql          # -> gold_pii schema
      _core__models.yml  _sales__models.yml  ...
  snapshots/       customer_snapshot.sql  product_snapshot.sql  store_snapshot.sql  account_snapshot.sql
  seeds/           country_codes.csv  channel_map.csv  category_map.csv  store_master.csv  currency_list.csv
  macros/          surrogate_key.sql  optimize_table.sql  qualify_dedupe.sql  to_usd.sql  env_schema.sql
  tests/           assert_order_equals_lines.sql  assert_no_pii_in_gold.sql
                   recon_row_counts.sql  recon_gmv_control_total.sql  recon_refund_balancing.sql
  analyses/
```

- **One project**, domains as subfolders under `marts/` - because `10` (split
  only if build time > 35 min, `09`).
- **Mono-repo** with `infra/`, `dagster/`, `extractors/` - because `10`.

## 2. Layer model

| Layer | Name | Contents | Materialisation | Grain | Schema |
|-------|------|----------|-----------------|-------|--------|
| Staging | `stg_<src>__<entity>` | 1:1 with a `bronze` object; rename, cast, trim, drop `test`/`_superseded`/`is_deleted` | **view** | source row | `silver` |
| Intermediate | `int_<domain>__<step>` | identity resolution, currency->USD, channel union, dedupe, business rules | **ephemeral** | varies | `silver` |
| Marts | `dim_*` / `fct_*` / `agg_*` | consumer-facing | **table** (dims/aggs) / **incremental merge** (big facts) | stated per table | `gold` / `gold_pii` |

Maps to lakehouse `bronze` (landed, not dbt) -> `silver` -> `gold`/`gold_pii` -
because `02`, `03`.

## 3. Sources & freshness

| Source (`sources.yml`) | Landed table | `loaded_at_field` | warn_after | error_after |
|------------------------|--------------|-------------------|-----------|-------------|
| `oltp.*` | `bronze.oltp__*` | `_extracted_at` | 6h | 10h |
| `shopify.*` | `bronze.shopify__*` | `_extracted_at` | 4h | 8h |
| `pos.txn` | `bronze.pos__txn` | `_extracted_at` | 5h | 10h |
| `salesforce.*` | `bronze.sfdc__*` | `_extracted_at` | 10h | 18h |
| `ga4.session` | `bronze.ga4__session` | `_extracted_at` | 30h | 50h |
| `fx.rate` | `bronze.fx__rate` | `_extracted_at` | 8h | 30h |

`dbt source freshness` runs at the start of `curated_build` - a hard error blocks
the build - because `07` SLA + `01` cadence.

## 4. Materialisation & incremental strategy

| Model / group | Materialisation | Incremental strategy | `unique_key` | Partition / ZORDER | Because |
|---------------|-----------------|----------------------|--------------|--------------------|---------|
| `stg_*` | view | - | - | - | cheap, always fresh |
| `int_*` | ephemeral | - | - | - | no storage, inlined |
| `dim_*` | table | - | - | ZORDER by business key | small, full rebuild from snapshot |
| `fct_order` | incremental | `merge` | `order_id, channel` | partition `order_date`, ZORDER `customer_sk` | `02` load pattern, `09` volume |
| `fct_order_line` | incremental | `merge` | `order_id, line_no` | partition `order_date` | `02` |
| `fct_refund` | incremental | `merge` | `refund_id` | partition `refund_date` | `02` |
| `fct_web_session` | incremental | `insert` (idempotent per `session_date` via `delete+insert`) | `session_id, session_date` | partition `session_date` | `02`, GA4 shard reprocess |
| `fct_wholesale_opportunity` | incremental | `merge` | `opportunity_id` | partition `close_date` | `02`, Q4 |
| `agg_*` | table | - | - | - | full rebuild daily, cheap |

- **Incremental filter:** `WHERE order_date >= (SELECT max(order_date) FROM
  {{ this }}) - INTERVAL 3 DAYS` (late-arriving lookback) unless
  `--vars business_date` forces an exact date (scheduled + backfill runs).
- **Full-refresh policy:** allowed in `dev`; in `stg`/`prd` only via a tagged
  release + on-call approval.

## 5. History / SCD2 (dbt snapshots)

| Entity | Snapshot | Strategy | Tracked columns | Because |
|--------|----------|----------|-----------------|---------|
| customer | `customer_snapshot` | `timestamp` on `updated_at` | country_iso, loyalty_tier, is_marketable | `03` |
| customer PII | `customer_snapshot` (same) feeds `dim_customer_pii` | `timestamp` | email, phone, name, address, dob | `03`, `08` |
| product | `product_snapshot` | `timestamp` | price, category, brand, status | `03` |
| store | `store_snapshot` | `check` on all cols | region, tz, status | `03` |
| account | `account_snapshot` | `timestamp` on `SystemModstamp` | name, segment, country | `03` |

`dim_*` models select `is_current` + full history from the snapshot; a
continuity test asserts no `dbt_valid_to` gaps.

## 6. Data quality as tests

| Check type | How | Runs in | Fails the build? |
|------------|-----|---------|------------------|
| Generic (`not_null`, `unique`, `accepted_values`, `relationships`) | `_models.yml` on every key + enum (area 04) | every run + CI | yes (error severity) |
| Expectations (ranges, regex, row counts, distribution) | `dbt_expectations` - `expect_column_values_to_match_regex` (email_hash), `_to_be_between` (amounts, dates), `_row_count` | every run | yes above threshold |
| Freshness | `dbt source freshness` | pre-run | yes |
| Anomaly / volume | `elementary` - row count, null rate, GMV per channel | every run | warn -> Slack; hard anomaly -> page |
| Singular | `tests/assert_order_equals_lines.sql`, `assert_no_pii_in_gold.sql` | every run | yes |

- Rule-to-test mapping is the table in `requirements/04-data-quality.md` - each
  row is a test entry in a `_models.yml` or `tests/`.
- **Severity:** `severity: error` for keys, identity, PII-leak, order=lines;
  `severity: warn` (with `error_if: ">50"`) for soft rules.
- **Quarantine:** rows failing a routing rule are written to
  `silver.reject__<entity>` with `reason_code`; a singular test fails the build
  if `reject_count / batch_count > 0.005`.

## 7. Reconciliation hooks

- Reconciliation checks from `requirements/05` are **singular tests** in
  `tests/`:
  - `recon_row_counts.sql` - source extracted (from manifest) == bronze ==
    silver in + rejected + superseded, per source/date;
  - `recon_gmv_control_total.sql` - `SUM(net_amount_usd)` per channel/date vs the
    control-total table, fail if `abs(delta) > 0.005 * control`;
  - `recon_refund_balancing.sql` - every refund links to an order; sum per
    customer/period within tolerance.
- These run in a dedicated `dbt test --select tag:recon` step that Dagster wraps
  in the **`reconcile` asset check**; FAIL => `publish` asset not materialised
  (exit non-zero) - because `05` hard gate.
- `audit_helper.compare_relations` used ad-hoc for source-to-`gold` parity during
  incident triage.

## 8. Packages, macros, seeds

| Package | Used for |
|---------|----------|
| `dbt_utils` | `generate_surrogate_key`, `star`, `union_relations`, `equality` |
| `dbt_expectations` | range / regex / distribution / row-count tests |
| `elementary` | DQ report site, anomaly detection, test history |
| `dbt_date` | `dim_date`, fiscal period logic |
| `codegen` | dev-only: scaffold staging models + `sources.yml` |

- **Project macros:** `surrogate_key()` (wraps `generate_surrogate_key` so the
  hash impl is swappable), `to_usd(amount, currency, date)` (joins
  `dim_fx_rate`, carry-forward aware), `env_schema()` (prefixes schema per
  `--target`), `optimize_table()` (`OPTIMIZE ... ZORDER BY`, Databricks-only,
  called in a weekly maintenance job not per run), `qualify_dedupe()`
  (`QUALIFY row_number() ...` with a DuckDB fallback for tests).
- **Seeds:** the 5 CSVs from `requirements/03`; changed only via PR; a schema
  test guards each.

## 9. Docs, exposures, lineage

- `dbt docs generate` on every prd release -> static site in
  `s3://northwind-prd-dbt-docs` behind Okta - because `06` catalog / glossary.
- **Exposures:** `looker_sales` (depends on `fct_order`, `fct_order_line`,
  `dim_*`), `braze_segments` (`dim_customer`, `agg_customer_monthly`),
  `finance_close` (`agg_sales_daily`, `fct_refund`). A breaking change to an
  exposed model triggers the 10-day consumer notice (`06`).
- dbt `manifest.json` + `catalog.json` pushed to the OpenLineage endpoint and
  UC column comments set from `_models.yml` - because `06` column-level lineage.

## 10. Run interface

- **Per-pipeline invocation (Dagster / CI):**
  `dbt build --select <selector> --target <env> --vars '{business_date: <D>, run_id: <uuid>}'`
- **Selectors:**
  - `curated_build`: `dbt build --select staging+ intermediate+ marts+ --exclude tag:recon`
  - `reconcile`: `dbt test --select tag:recon --target <env>`
  - per-source dev iteration: `dbt build --select stg_pos__* +int_sales__order_store +`
- **Slim CI:** `dbt build --select state:modified+ --defer --state ./prod-manifest`
  - because `10` slim-CI requirement.
- **Where it runs:** Dagster job-compute cluster (scheduled) / GitHub Actions
  runner against a CI schema in `northwind_dev` (PR) - because `07`, `10`.

## 11. Open questions

| Q# | Impact on the transformation layer |
|----|------------------------------------|
| Q2 | backfill selector runs one `business_date` at a time; 12 vs 24 months only changes iteration count |
| Q4 | `int_sales__order_wholesale` + `fct_wholesale_opportunity` grain; the `wholesale` branch of `recon_gmv_control_total` stays `severity: warn` until confirmed |
