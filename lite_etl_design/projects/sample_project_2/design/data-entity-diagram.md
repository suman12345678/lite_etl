# Data-entity diagram (ER) - Northwind Commerce (DEMO)

> Mermaid `erDiagram`. `gold` target model first, then `gold_pii`, then key
> `silver` staging entities. Names match `02-targets-and-loading.md` and
> `03-transformations.md`.

## gold target model

```mermaid
erDiagram
  DIM_CUSTOMER ||--o{ FCT_ORDER : places
  DIM_STORE    ||--o{ FCT_ORDER : "sold at"
  DIM_DATE     ||--o{ FCT_ORDER : "ordered on"
  DIM_ACCOUNT  ||--o{ FCT_WHOLESALE_OPPORTUNITY : holds
  FCT_ORDER    ||--o{ FCT_ORDER_LINE : "has"
  DIM_PRODUCT  ||--o{ FCT_ORDER_LINE : "sells"
  FCT_ORDER    ||--o{ FCT_REFUND : "refunded by"
  DIM_CUSTOMER ||--o{ FCT_WEB_SESSION : "browsed in"
  DIM_FX_RATE  ||--o{ FCT_ORDER : "converted with"

  DIM_CUSTOMER {
    string  customer_sk PK "surrogate = generate_surrogate_key(customer_bk)"
    string  customer_bk  "sha256(salt||lower(email)) or loyalty_id"
    string  email_hash   "sha256, ^[a-f0-9]{64}$"
    string  country_iso
    string  loyalty_tier
    string  age_band     "18-24 / 25-34 / ..."
    boolean is_marketable
    boolean is_erased    "RTBF tombstone"
    date    dbt_valid_from "SCD2"
    date    dbt_valid_to   "SCD2"
    boolean is_current     "SCD2"
  }

  FCT_ORDER {
    string  order_id PK
    string  channel PK "web / store / wholesale"
    string  customer_sk FK
    string  store_sk FK "= -1 for non-store"
    int     date_key FK
    string  currency
    decimal gross_amount_usd
    decimal discount_amount_usd
    decimal tax_amount_usd
    decimal net_amount_usd "= gmv"
    decimal margin_usd
    boolean is_return
    string  source_run_id "lineage"
    string  dbt_model_sha "lineage"
  }

  FCT_ORDER_LINE {
    string  order_id FK
    int     line_no PK
    string  product_sk FK
    int     quantity
    decimal unit_price_usd
    decimal net_amount_usd
    decimal cogs_usd
  }

  FCT_REFUND {
    string  refund_id PK
    string  order_id FK
    int     refund_date_key FK
    decimal refund_amount_usd "always >= 0"
    string  reason
  }

  FCT_WEB_SESSION {
    string  session_id PK
    int     session_date_key PK
    string  customer_sk FK "-1 if unmatched"
    string  channel_group
    int     events
    int     conversions
    decimal revenue_usd
  }

  FCT_WHOLESALE_OPPORTUNITY {
    string  opportunity_id PK
    string  account_sk FK
    int     close_date_key FK
    string  stage
    decimal amount_usd "fulfillment grain (Q4 assumption)"
  }

  DIM_PRODUCT {
    string product_sk PK
    string product_id
    string category
    string brand
    decimal list_price_usd
    date   dbt_valid_from
    date   dbt_valid_to
    boolean is_current
  }

  DIM_STORE {
    string store_sk PK
    string store_id
    string region
    string store_tz
    date   opened_date
    date   dbt_valid_from
    date   dbt_valid_to
  }

  DIM_ACCOUNT {
    string account_sk PK
    string sfdc_account_id
    string account_name
    string segment
    string country_iso
    date   dbt_valid_from
    date   dbt_valid_to
  }

  DIM_FX_RATE {
    date    rate_date PK
    string  currency PK
    decimal rate_to_usd
    boolean is_carried_forward
  }

  DIM_DATE {
    int  date_key PK
    date calendar_date
    int  fiscal_period
  }
```

## gold_pii (restricted - UC row filter + column mask)

```mermaid
erDiagram
  DIM_CUSTOMER ||--|| DIM_CUSTOMER_PII : "same customer_sk"

  DIM_CUSTOMER_PII {
    string customer_sk PK "= DIM_CUSTOMER.customer_sk"
    string customer_bk
    string email        "real - masked column"
    string phone_e164   "real - masked column"
    string full_name    "real"
    string address_line1
    string address_line2
    string postcode
    date   date_of_birth
    date   dbt_valid_from
    date   dbt_valid_to
    boolean is_current
  }
```

## Key silver staging entities

```mermaid
erDiagram
  STG_SHOPIFY__ORDERS {
    string order_id
    timestamp updated_at "watermark"
    string presentment_currency
    decimal presentment_total
    string customer_email_raw
    boolean is_test
    string _run_id
    string _dq_status "pass / reject"
  }

  STG_POS__TXN {
    string txn_id
    string store_id
    date   business_date "dt partition"
    timestamp txn_ts_utc
    decimal amount_usd "cents/100"
    string _file_etag
    boolean _superseded
    string _run_id
  }

  INT_CUSTOMER__RESOLVED {
    string customer_bk
    string source_system "oltp>shopify>salesforce priority"
    timestamp updated_at
    string email_hash
    string country_iso
  }
```

## Notes

- **Keys:** all dims use a hashed-business-key surrogate
  (`dbt_utils.generate_surrogate_key`); every dim seeds an unknown-member row
  `_sk = -1`. Facts carry natural keys + resolved `_sk`s.
- **Grain:** `FCT_ORDER` = one order per channel; `FCT_ORDER_LINE` = order line;
  `FCT_REFUND` = refund; `FCT_WEB_SESSION` = session per session_date;
  `FCT_WHOLESALE_OPPORTUNITY` = opportunity at fulfillment grain (Q4).
- **Historisation:** `DIM_CUSTOMER/PRODUCT/STORE/ACCOUNT` are SCD2 via dbt
  snapshots; `DIM_FX_RATE` is upsert; facts are not versioned (late corrections
  `merge` on key).
- **Lineage columns:** `source_run_id` + `dbt_model_sha` carried into every fact
  per `06`.
