# 04 - Data quality

> DEMO - fictional.

## Dimensions to enforce

| Dimension | Enforce? | Notes |
|-----------|----------|-------|
| Completeness | yes | BCBS 239 mandatory fields must be non-null on regulated feeds (final list Q1) |
| Validity | yes | ISO 4217 currency, IBAN check digit, date ranges, enum status codes |
| Uniqueness | yes | `account_id`, `customer_id`, `(txn_id, post_date)`, `(gl_account, cost_centre, business_date)` |
| Consistency | yes | GL: debits == credits per journal; card `TOTAL` line vs parsed sum; balance_eur sign vs dr/cr |
| Referential integrity | yes | every `FACT_CARD_TXN.account_id` exists in current `DIM_ACCOUNT`; every `txn_ccy` in `DIM_FX_RATE` for `post_date` |
| Timeliness | yes | no `post_date` in the future (+1 day skew); file/feed freshness within SLA window |
| Accuracy | yes | IBAN/BBAN check digits; FX rate within 20% of prior day (else review) |

## Concrete rules

| Field / entity | Rule | Severity | On failure |
|----------------|------|----------|------------|
| `DIM_ACCOUNT.account_id` | not null, unique | error | fail run |
| `DIM_ACCOUNT.currency` | in ISO 4217 list | error | quarantine row |
| `DIM_ACCOUNT.iban` | valid check digits (when present) | warn | quarantine row + flag |
| `DIM_CUSTOMER.date_of_birth` | not `1900-01-01`; age 18-120 | warn | set null + DQ flag |
| `DIM_CUSTOMER.national_id` | matches country format | warn | quarantine row |
| `FACT_CARD_TXN (txn_id, post_date)` | unique | error | dedupe, log to recon |
| `FACT_CARD_TXN.amount` | numeric, `abs(amount) <= 1_000_000` | error | quarantine row |
| `FACT_CARD_TXN.post_date` | not future (+1d), within business_date -35d | error | quarantine row |
| `FACT_CARD_TXN.account_id` | exists in current `DIM_ACCOUNT` | error | quarantine row |
| `FACT_CARD_TXN.txn_ccy` | has an FX rate for `post_date` | error | quarantine row |
| `FACT_GL_BALANCE` per journal | sum(debits) == sum(credits) | error | fail run (blocks publish) |
| `DIM_FX_RATE` | <= 4 consecutive carry-forward days | error | fail run |
| all regulated feeds | BCBS 239 mandatory fields non-null | error | fail run if > threshold |

## Thresholds

- **Fail the run** if reject rate on a **regulated feed** (`core_banking_accounts`,
  `general_ledger`, `customer_master`) > **0.1%** of rows for the business date.
- **Fail the run** if `card_transactions` reject rate > **0.5%** OR any GL
  journal fails debits==credits (zero tolerance).
- **Warn** (alert, do not block) at half the fail threshold.
- Evaluated **per business date, per source** (not per partition file).

## Reporting & ownership

- **DQ report:** `_dq_report.json` per run + a daily rollup table
  `CURATED.DQ_DAILY` (rule, rows checked, rows failed, action, run_id). A Slack
  digest to `#risk-data-ops` at 06:15 CET.
- **DQ score:** per feed = 1 - (weighted failed rows / rows checked); tracked
  over time; < 0.995 on a regulated feed triggers a review ticket.
- **Owner of source-data fixes:** the source system owner in `01`; Risk Data
  raises the ticket, tracks quarantine drain via reprocessing.
