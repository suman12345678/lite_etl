# 05 - Reconciliation

> DEMO - fictional. Reconciliation is the hard publish gate for this harness.

## Checks

| Check | Applies to | Tolerance | On failure |
|-------|-----------|-----------|------------|
| Row counts: `source == landed + rejected + filtered` | every source, per business date | exact | block publish |
| Row counts: `landed == staged == curated` (minus documented filters) | all | exact | block publish |
| Control total: `SUM(amount)` by `txn_ccy` | `card_transactions` parsed vs file `TOTAL` trailer line | exact (minor units) | block publish |
| Control total: `SUM(amount_eur)`, `COUNT` | card txn landing vs curated `FACT_CARD_TXN` | 0.01 EUR rounding band | block publish |
| Financial balance: `SUM(debits) == SUM(credits)` per journal | `general_ledger` | exact | block publish |
| GL movement: `opening_balance + SUM(movements) == closing_balance` per `(gl_account, cost_centre, business_date)` | `general_ledger` | exact | block publish |
| Sub-ledger tie-out: `SUM(FACT_ACCOUNT_BALANCE_DAILY.balance_eur)` by GL mapping vs `FACT_GL_BALANCE` closing | cross-source | <= 1 EUR per GL account | **warn + alert Finance** (not block - documented reconciling items expected initially) |
| Referential coverage: all curated `account_id` covered by `DIM_ACCOUNT` | card + balance facts | exact | block publish |
| Duplicate check: no unexpected `(txn_id, post_date)` duplicates in curated | `FACT_CARD_TXN` | exact | block publish |
| Distribution drift: row count & `SUM(amount_eur)` vs trailing 20-business-day mean | card + balances | +/- 25% => review | warn + alert |
| FX completeness: every curated `post_date` currency has a rate | conversions | exact | block publish |

## Gate behaviour

- A hard failure: **no `_SUCCESS` marker, no publish to `CURATED`**, the Airflow
  task fails, business date stays "open".
- Pipeline / CLI exits non-zero on failure.
- **Auto-retry:** only the *extract* and *land* tasks retry (3x). Reconciliation
  itself does not auto-retry - a FAIL needs a human decision (fix source, accept
  documented break with sign-off, or re-run).

## Authoritative control report

- **Card:** the `TOTAL` trailer line inside each daily file (count + sum in
  minor units) is the control total.
- **GL:** `gl_journal_header` control totals from the BigQuery replica.
- **Regulatory:** monthly, Regulatory Reporting provides expected aggregate
  balances by regulatory bucket; a monthly recon job compares (report only).

## Granularity

Per `(source, business_date)` for daily checks; per journal for GL balance;
per GL account for the sub-ledger tie-out; monthly for the regulatory aggregate.
