# dbt project scaffold - Northwind Commerce (DEMO)

> Phase 3 deliverable. The concrete dbt project tree under `build/repo/dbt/`, and
> the map from each model / test / snapshot / seed to the Phase 2 design section.

- **Framework / adapter:** dbt Core 1.8; `dbt-databricks` (dev/stg/prd),
  `dbt-duckdb` (`ci`)
- **Design baseline:** `design/transformation-design.md`,
  `design/data-entity-diagram.md`, `requirements/03`, `requirements/04`

## Tree to create

```
build/repo/dbt/
  dbt_project.yml
  packages.yml
  profiles/profiles.yml            # targets: ci (duckdb), dev, stg, prd
  models/
    staging/
      oltp/      stg_oltp__customers.sql  stg_oltp__products.sql  stg_oltp__orders.sql  stg_oltp__order_lines.sql
                 _oltp__sources.yml  _oltp__models.yml
      shopify/   stg_shopify__orders.sql  stg_shopify__refunds.sql  stg_shopify__fulfillments.sql
                 _shopify__sources.yml  _shopify__models.yml
      pos/       stg_pos__txn.sql  stg_pos__txn_line.sql  _pos__sources.yml  _pos__models.yml
      salesforce/ stg_sfdc__account.sql  stg_sfdc__contact.sql  stg_sfdc__opportunity.sql  stg_sfdc__opportunity_line.sql
                 _sfdc__sources.yml  _sfdc__models.yml
      ga4/       stg_ga4__session.sql  _ga4__sources.yml  _ga4__models.yml
      fx/        stg_fx__rate.sql  _fx__sources.yml  _fx__models.yml
    intermediate/
      customer/  int_customer__resolved.sql  int_customer__pii.sql
      sales/     int_sales__order_web.sql  int_sales__order_store.sql  int_sales__order_wholesale.sql
                 int_sales__order_unioned.sql  int_sales__lines.sql  int_sales__refunds.sql
      fx/        int_fx__daily.sql
      web/       int_web__session.sql
    marts/
      core/      dim_customer.sql  dim_product.sql  dim_store.sql  dim_account.sql  dim_fx_rate.sql  dim_date.sql  _core__models.yml
      sales/     fct_order.sql  fct_order_line.sql  fct_refund.sql  agg_sales_daily.sql  agg_customer_monthly.sql  _sales__models.yml
      web/       fct_web_session.sql  _web__models.yml
      wholesale/ fct_wholesale_opportunity.sql  _wholesale__models.yml
      pii/       dim_customer_pii.sql  _pii__models.yml     # -> gold_pii schema
  snapshots/     customer_snapshot.sql  product_snapshot.sql  store_snapshot.sql  account_snapshot.sql
  seeds/         country_codes.csv  channel_map.csv  category_map.csv  store_master.csv  currency_list.csv
  macros/        surrogate_key.sql  optimize_table.sql  qualify_dedupe.sql  to_usd.sql  env_schema.sql
  tests/         assert_order_equals_lines.sql  assert_no_pii_in_gold.sql
                 recon_row_counts.sql  recon_gmv_control_total.sql  recon_refund_balancing.sql
```

## Model map

| dbt object | File | Implements (design ref) | Materialisation | Tests attached |
|------------|------|-------------------------|-----------------|----------------|
| `stg_oltp__*` (4) | `models/staging/oltp/` | transformation-design s.2; `03` cleansing | view | `not_null`+`unique` on key; drop `is_deleted` |
| `stg_shopify__orders` etc. (3) | `models/staging/shopify/` | `03`; `01` quirks (multi-currency, `test=true`) | view | `not_null` key; `test` count == 0 |
| `stg_pos__txn` / `stg_pos__txn_line` | `models/staging/pos/` | `03` (cents/100, tz->UTC, supersede) | view | latest non-superseded etag per `(dt,store)` |
| `stg_sfdc__*` (4) | `models/staging/salesforce/` | `03`; `01` | view | `not_null` key |
| `stg_ga4__session` | `models/staging/ga4/` | `03` (dedupe, 0-event drop) | view | `unique (session_id, session_date)` |
| `stg_fx__rate` | `models/staging/fx/` | `03` (carry-forward) | view | `not_null (rate_date, currency)` |
| `int_customer__resolved` | `models/intermediate/customer/` | `03` identity (`sha256`, source priority) | ephemeral | - |
| `int_customer__pii` | `models/intermediate/customer/` | `03`/`08` PII split | ephemeral | - |
| `int_sales__order_{web,store,wholesale}` | `models/intermediate/sales/` | `03` per-channel rules; Q4 for wholesale | ephemeral | - |
| `int_sales__order_unioned` / `int_sales__lines` / `int_sales__refunds` | `models/intermediate/sales/` | `03` | ephemeral | - |
| `int_fx__daily` | `models/intermediate/fx/` | `03` (fill gaps) | ephemeral | - |
| `int_web__session` | `models/intermediate/web/` | `03` (attribute to `customer_sk` or -1) | ephemeral | - |
| `dim_customer` | `models/marts/core/` | data-entity-diagram; `02` SCD2 | table | `unique customer_sk`, `email_hash` regex `^[a-f0-9]{64}$` |
| `dim_product` / `dim_store` / `dim_account` | `models/marts/core/` | ER; `02` SCD2 (snapshot-backed) | table | `unique` sk; `relationships` |
| `dim_fx_rate` | `models/marts/core/` | ER; `02` upsert | table | `unique (rate_date, currency)` |
| `dim_date` | `models/marts/core/` | ER | table | `unique date_key` (built via `dbt_date`) |
| `fct_order` | `models/marts/sales/` | ER (grain: order/channel); `02` merge | incremental (`merge`, `unique_key=[order_id,channel]`, partition `order_date`) | `not_null` FKs; `accepted_values(channel)`; `dbt_expectations` amount ranges; singular `assert_order_equals_lines` |
| `fct_order_line` | `models/marts/sales/` | ER (grain: line) | incremental (`merge`, `[order_id,line_no]`) | `not_null`; `relationships` to `fct_order` |
| `fct_refund` | `models/marts/sales/` | ER; `05` refund balancing | incremental (`merge`, `refund_id`) | `refund_amount_usd >= 0`; `relationships` to `fct_order` |
| `agg_sales_daily` / `agg_customer_monthly` | `models/marts/sales/` | `03` aggregations | table (full rebuild) | row-count `dbt_expectations` |
| `fct_web_session` | `models/marts/web/` | ER; `03` | incremental (`delete+insert` per `session_date`) | `unique (session_id, session_date)` |
| `fct_wholesale_opportunity` | `models/marts/wholesale/` | ER; Q4 grain=fulfillment | incremental (`merge`, `opportunity_id`) | `not_null`; `TODO` recognition rule |
| `dim_customer_pii` | `models/marts/pii/` (schema `gold_pii`) | `08` PII split; ER | table | `unique customer_sk`; singular `assert_no_pii_in_gold` (leak guard on `gold.*`) |
| `*_snapshot` (4) | `snapshots/` | transformation-design s.5 | snapshot (`strategy=timestamp`/`check`) | `dbt_valid_to` continuity singular |
| seeds (5) | `seeds/` | `03` reference data | seed | `accepted_values` on codes |

## Macros to create

| Macro | Purpose | Design ref |
|-------|---------|-----------|
| `surrogate_key(cols)` | wrap `dbt_utils.generate_surrogate_key` so the hash impl is swappable | transformation-design s.8 |
| `to_usd(amount, currency, date_col)` | join `dim_fx_rate` at the date, carry-forward aware | `03` currency conversion |
| `qualify_dedupe(partition_by, order_by)` | `QUALIFY row_number()...` with a DuckDB fallback | portability stance (`10`) |
| `optimize_table()` | `OPTIMIZE ... ZORDER BY` - Databricks only, called from a weekly maintenance job, **not** per run | `09` cost |
| `env_schema(base)` | prefix schema per `--target` (`gold` vs `gold_pii`, env isolation) | `10` |

## Run targets

- `make dbt-ci` -> `dbt build --target ci` (DuckDB, seeds + fixtures as `bronze`).
- `dbt build --select <selector> --target dev` - per-pipeline (Phase 4).
- `dbt test --select tag:recon` - the reconciliation gate step (component 6).

## Fixtures for `--target ci`

`tests/conftest.py` loads `build/repo/tests/fixtures/<src>/sample.*` into DuckDB
tables named `bronze.<src>__<obj>` before `dbt build --target ci`. The `ci`
profile points dbt at that DuckDB file. Golden outputs in `tests/golden/`
(`fct_order.csv`, `dim_customer.csv`) diffed by `make golden`.

## Note - stubs only

Every `.sql` file in the scaffold has: a header comment citing its design ref, a
`{{ config(...) }}` block with the materialisation/keys/partition from the table
above, `_sources.yml`/`_models.yml` skeletons with the **known** columns (from
`01`) and the named tests, and a `-- TODO:` for the SELECT body. `dbt parse`
succeeds; `dbt build` bodies are for Phase 3 implementation, not this scaffold.
