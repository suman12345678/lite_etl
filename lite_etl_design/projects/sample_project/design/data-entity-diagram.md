# Data-entity diagram - Meridian Trust (DEMO)

> Produced by `/design-architecture` on 2026-09-03. Entity/attribute names match
> `../requirements/02-targets-and-loading.md` and `03-transformations.md`.

## CURATED model (target)

```mermaid
erDiagram
  DIM_ACCOUNT   ||--o{ FACT_CARD_TXN            : "account_sk"
  DIM_ACCOUNT   ||--o{ FACT_ACCOUNT_BALANCE_DAILY : "account_sk"
  DIM_CUSTOMER  ||--o{ DIM_ACCOUNT               : "owns (customer_sk)"
  DIM_DATE      ||--o{ FACT_CARD_TXN             : "post_date_sk"
  DIM_DATE      ||--o{ FACT_ACCOUNT_BALANCE_DAILY : "business_date_sk"
  DIM_DATE      ||--o{ FACT_GL_BALANCE           : "business_date_sk"
  DIM_FX_RATE   ||--o{ FACT_CARD_TXN             : "rate_date + ccy"
  DIM_GL_ACCOUNT ||--o{ FACT_GL_BALANCE          : "gl_account_sk"
  DIM_CUSTOMER  ||--|| CUSTOMER_SENSITIVE        : "customer_sk (restricted)"

  DIM_ACCOUNT {
    string  account_sk PK "sha256(account_id)"
    string  account_id   "business key"
    string  customer_id  FK
    string  product_code
    string  product_group
    string  status       "OPEN|DORMANT|CLOSED"
    string  currency     "ISO 4217"
    string  branch_code
    string  iban
    date    valid_from   "SCD2 (LAST_MOD_TS)"
    date    valid_to     "SCD2"
    boolean is_current   "SCD2"
    string  _source_run_id
  }

  DIM_CUSTOMER {
    string  customer_sk PK "sha256(customer_id)"
    string  customer_id
    string  full_name_token  "FPE token"
    string  dob_token        "date-preserving token"
    string  national_id_token
    string  country
    string  segment
    string  risk_rating
    string  kyc_status
    date    valid_from
    date    valid_to
    boolean is_current
  }

  CUSTOMER_SENSITIVE {
    string customer_sk PK "-> DIM_CUSTOMER"
    string full_name   "REAL - CURATED_SENSITIVE only, row-access policy"
    date   date_of_birth
    string national_id
    string address_line1
    string address_city
    string address_country
    date   valid_from
    date   valid_to
    boolean is_current
  }

  FACT_CARD_TXN {
    string  txn_id PK
    date    post_date PK
    string  account_sk FK
    string  post_date_sk FK
    string  pan_last4
    string  mcc
    string  merchant_category
    decimal amount        "DECIMAL(18,2), txn ccy"
    string  txn_ccy
    decimal amount_eur    "converted via DIM_FX_RATE"
    boolean is_international
    boolean is_reversal
    string  _source_run_id
    string  _dbt_invocation_id
  }

  FACT_ACCOUNT_BALANCE_DAILY {
    string  account_sk PK
    date    business_date PK
    string  business_date_sk FK
    decimal balance        "account ccy"
    string  currency
    decimal balance_eur
    boolean carried_forward
    string  _source_run_id
  }

  FACT_GL_BALANCE {
    string  gl_account_sk PK
    string  cost_centre PK
    date    business_date PK
    string  business_date_sk FK
    decimal opening_balance_eur
    decimal movements_eur
    decimal closing_balance_eur
    string  _source_run_id
  }

  DIM_FX_RATE {
    date    rate_date PK
    string  ccy PK
    decimal rate_to_eur
    boolean is_carried_forward
  }

  DIM_GL_ACCOUNT {
    string gl_account_sk PK
    string gl_account
    string gl_account_name
    string gl_level1
    string gl_level2
  }

  DIM_DATE {
    string  date_sk PK
    date    calendar_date
    boolean is_target_business_day
    int     fiscal_period
  }
```

## Key STAGING entities

```mermaid
erDiagram
  STG_CARD_TXN {
    string txn_id
    date   post_date
    string account_id       "natural, pre-join"
    string pan_last4
    decimal amount
    string txn_ccy
    string mcc
    string _run_id
    string _dq_status        "pass | fixed | reject"
    string _reason_code      "when reject"
  }
  STG_ACCOUNT {
    string account_id
    string customer_id
    string product_code
    string status_raw
    string status_clean
    string ccy_raw
    string ccy_iso
    timestamp last_mod_ts    "watermark, UTC"
    string _run_id
    string _dq_status
  }
  STG_GL_BALANCE {
    string gl_account
    string cost_centre
    date   business_date
    string dr_cr
    decimal amount_eur_signed
    string journal_id
    string _run_id
  }
```

## Notes

- **Grain:** `FACT_CARD_TXN` = one card transaction (`txn_id`, `post_date`);
  `FACT_ACCOUNT_BALANCE_DAILY` = one account per business date;
  `FACT_GL_BALANCE` = one GL account / cost centre per business date.
- **SCD2** on `DIM_ACCOUNT`, `DIM_CUSTOMER`, `CUSTOMER_SENSITIVE` (`03`).
- **Lineage columns** `_source_run_id` / `_dbt_invocation_id` on every fact and
  dim (`06`).
- `CUSTOMER_SENSITIVE` lives in `CURATED_SENSITIVE`, 1:1 with `DIM_CUSTOMER` on
  `customer_sk`, behind a Snowflake row-access policy (`08`).
