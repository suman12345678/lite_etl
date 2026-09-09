# 03 - Transformations

> DEMO - fictional. Business rules here; the dbt project mechanics (layers,
> materialisations, tests, packages) are in `10-platform-and-deployment.md`.

- **ETL or ELT:** **ELT** - extractors land raw bytes/rows in `bronze`; all
  transformation runs as **dbt models in Databricks** (`silver` -> `gold`). The
  only pre-load logic is decomp/parse (POS CSV), Shopify JSON flattening, and
  GA4 aggregation, done in the extract step.
- **Transformation tooling:** dbt Core 1.8 with `dbt-databricks`. See area 10.

## Per-entity transformation rules

### Entity: `gold.dim_customer` (+ `gold_pii.dim_customer_pii`)

- **Source(s):** `oltp.customers`, `shopify` order customer blocks, `salesforce`
  contacts (wholesale buyers)
- **Cleansing:** trim, collapse whitespace, lower-case email, E.164 phone,
  title-case name, ISO-3166 country via `country_codes` seed
- **Standardisation:** channel via `channel_map`; loyalty tier lookup
- **Deduplication:** business key `customer_bk` = `sha256(salt || lower(trim(email)))`
  or `loyalty_id` when present; winning record = latest `updated_at` across
  sources, source priority `oltp > shopify > salesforce` on ties
- **Joins / enrichment:** first_order_date, lifetime_orders, lifetime_gmv from
  `fct_order`
- **Business rules:** `is_marketable` = consent flag AND not RTBF-tombstoned
- **Historisation:** SCD2 via dbt snapshot on `customer_bk`, tracked columns:
  country, loyalty_tier, is_marketable; `dbt_valid_from/to`
- **PII split:** hashed email + non-identifying attrs in `gold.dim_customer`;
  real email/phone/name/address/DOB only in `gold_pii.dim_customer_pii`
  (same `customer_sk`)
- **Rejected rows:** no email AND no loyalty_id -> quarantine (`silver` reject
  table + reason `no_identity`)

### Entity: `gold.dim_product`

- **Source(s):** `oltp.products`
- **Cleansing:** trim; cast price to `decimal(12,2)`; null-out negative prices
- **Standardisation:** category hierarchy via `category_map` seed
- **Historisation:** SCD2 snapshot on `product_id`, track price, category, brand,
  status
- **Rejected rows:** missing `product_id` -> reject `bad_product_key`

### Entity: `gold.fct_order` / `gold.fct_order_line`

- **Source(s):** `oltp.orders`/`order_lines` (channel `store`? no - `web`? no:
  OLTP is the ecommerce+wholesale OLTP), `shopify` (channel `web`), `pos`
  (channel `store`), `salesforce` opportunities feed `fct_wholesale_opportunity`
  not `fct_order`
- **Cleansing:** POS amounts `cents / 100` -> `decimal(12,2)`; drop Shopify
  `test=true`; convert `txn_ts` (store-local + `store_tz`) to UTC and to
  `order_date` (store-local calendar date)
- **Standardisation:** currency -> USD using `dim_fx_rate` at `order_date`
  (carry-forward rate if missing); `gross_amount`, `discount_amount`,
  `tax_amount`, `net_amount`, `shipping_amount` normalised
- **Deduplication:** `fct_order` key `order_id`; POS supersede: keep rows from
  the latest non-superseded `file_etag` for `(dt, store)`; Shopify: latest
  `updated_at` per `order_id`
- **Joins / enrichment:** `customer_sk`, `product_sk`, `store_sk`, `date_key`
- **Business rules / derived measures:** `gmv` = net_amount in USD;
  `is_return` when linked refund fully offsets; `margin` = net_amount - cogs
  (cogs from product cost, snapshot-aligned)
- **Historisation:** facts are not SCD2; late corrections `merge` on key
- **Aggregations:** `gold.agg_sales_daily` (channel x store x date) and
  `gold.agg_customer_monthly` built from `fct_order`
- **Rejected rows:** order with unresolvable `customer_bk` -> load with
  `customer_sk = -1` (unknown member) + DQ warn; negative `gmv` not from a
  refund -> reject `impossible_amount`

### Entity: `gold.fct_refund`

- **Source(s):** `shopify` refunds, `oltp` returns
- **Rules:** always positive amount; `refund_date` = processed date; links to
  `order_id`; a refund without a matching order -> quarantine `orphan_refund`

### Entity: `gold.fct_web_session`

- **Source(s):** `ga4` aggregated sessions
- **Rules:** dedupe on `(session_id, session_date)`; attribute to `customer_sk`
  only when a `login` event carried a hashed email that matches `dim_customer`;
  else `customer_sk = -1`
- **Rejected rows:** session with 0 events -> drop (not a real session)

### Entity: `gold.dim_fx_rate`

- **Source(s):** `fx_rates`
- **Rules:** one row per `(rate_date, currency)`; fill weekend/holiday gaps by
  carrying the last rate forward, `is_carried_forward = true`

## Reference data needed

| Reference set | Source | Refresh | Used by |
|---------------|--------|---------|---------|
| `country_codes.csv` | ISO-3166 | rarely (PR) | dim_customer, dim_account |
| `channel_map.csv` | internal | on change | fct_order channel derivation |
| `category_map.csv` | Merchandising | monthly | dim_product |
| `store_master.csv` | Retail Ops | on store open/close | dim_store |
| `currency_list.csv` | Finance | rarely | dim_fx_rate validation |

## Surrogate key strategy

- Hash of business key via `dbt_utils.generate_surrogate_key` for all dimensions.
- Unknown-member row (`_sk = -1`) seeded into every dimension.
- Facts carry natural keys + resolved `_sk`s; no fact surrogate key.
