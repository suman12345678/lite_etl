# 03 - Transformations

> DEMO - fictional.

- **ETL or ELT:** **mixed.**
  - *ETL (Python, before load):* file parsing, decoding, PAN reduction,
    structural validation, tokenisation of PII, minor-unit -> decimal, type
    casting. Done in the landing/staging step so sensitive raw values never reach
    Snowflake in the clear.
  - *ELT (dbt in Snowflake, after load):* joins, SCD2 historisation, currency
    conversion, derived measures, dimensional model build.
- **Transformation tooling:** Python 3.11 + PyArrow for ETL; dbt-snowflake for ELT

## Per-entity transformation rules

### Entity: `DIM_ACCOUNT`  (from `core_banking_accounts`)

- **Cleansing:** trim, upper-case `CCY` -> ISO 4217; map `STATUS` codes to
  `{OPEN, DORMANT, CLOSED}`; drop `PRODUCT_CODE = 'ZZZ'` test accounts
- **Standardisation:** `PRODUCT_CODE` -> product name / product group via
  `chart of products` reference
- **Deduplication:** one row per `account_id` per extract; if both `ACCOUNT` and
  `ACCOUNT_BALANCE` changed, latest `LAST_MOD_TS` wins
- **Historisation:** **SCD2** on `product_code, status, currency, branch_code`;
  `valid_from` = `LAST_MOD_TS` (UTC), `valid_to`, `is_current`
- **Surrogate key:** `account_sk = sha256(account_id)`

### Entity: `DIM_CUSTOMER`  (from `customer_master`)

- **Cleansing:** trim; collapse address whitespace; replace `DateOfBirth`
  `1900-01-01` with NULL + DQ flag; normalise `NationalId` per country format
- **PII treatment (ETL step):** `full_name`, `date_of_birth`, `national_id` are
  **tokenised (FPE)** before landing. Real values land only in
  `CURATED_SENSITIVE` via a separate restricted path. See `08`.
- **Historisation:** **SCD2** on non-sensitive attributes (country, segment,
  risk_rating, kyc_status)
- **Surrogate key:** `customer_sk = sha256(customer_id)`

### Entity: `DIM_FX_RATE`  (from `fx_rates`)

- Base EUR; store `ccy`, `rate_to_eur`, `rate_date`
- **Carry-forward:** on a missing publication date, insert the last known rate
  with `is_carried_forward = TRUE` (max 4 consecutive days, then DQ error)

### Entity: `FACT_CARD_TXN`  (from `card_transactions`)

- **Parsing (ETL):** decode Windows-1252; strip header, trailing `TOTAL` line;
  amount = `raw_minor_units / 100` as `DECIMAL(18,2)`; `post_date` from
  `YYYYMMDD`; `pan_last4 = right(pan, 4)`, full PAN discarded
- **Standardisation:** `mcc` -> merchant category via reference; `txn_ccy` -> ISO
- **Deduplication:** key `(txn_id, post_date)`; if the split file repeats a row,
  keep first; log duplicates to reconciliation
- **Enrichment (ELT):** join `DIM_ACCOUNT` on `account_id` for account_sk,
  product, branch; `amount_eur = amount / DIM_FX_RATE.rate_to_eur` for `post_date`
- **Derived measures:** `is_international = txn_ccy <> 'EUR'`,
  `is_reversal = amount < 0`
- **Rejected rows:** quarantine (see 04); never silently dropped

### Entity: `FACT_GL_BALANCE`  (from `general_ledger`)

- Amounts already EUR; cast, standardise `dr_cr` to signed `amount_eur`
- Join `chart_of_accounts` for account hierarchy
- **No historisation** - daily snapshot; supports GL tie-out recon (05)

### Entity: `FACT_ACCOUNT_BALANCE_DAILY`  (from `core_banking_accounts`)

- One row per `account_id` per `business_date` (closing balance)
- `balance_eur = balance / DIM_FX_RATE.rate_to_eur` for `business_date`
- Accounts with no change that day carry forward prior closing balance

## Reference data needed

| Reference set | Source | Refresh | Used by |
|---------------|--------|---------|---------|
| Chart of products | core banking export | monthly | DIM_ACCOUNT |
| MCC -> merchant category | static CSV in repo | ad hoc | FACT_CARD_TXN |
| Country -> NationalId format | static CSV in repo | ad hoc | DIM_CUSTOMER |
| Chart of accounts | `general_ledger` (`chart_of_accounts`) | daily | FACT_GL_BALANCE |
| ISO 4217 currency list | static CSV in repo | ad hoc | validity checks |

## Surrogate key strategy

`sha256(business_key)` (deterministic, stable across reloads, no central
sequence). Facts carry natural keys + resolved `*_sk` from the dims.
