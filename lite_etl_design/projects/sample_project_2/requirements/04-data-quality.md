# 04 - Data quality

> DEMO - fictional. Rules are implemented as dbt tests - see
> `10-platform-and-deployment.md` s.6 and `design/transformation-design.md`.

## Dimensions to enforce

| Dimension | Enforce? | Notes |
|-----------|----------|-------|
| Completeness | yes | required fields per entity, fill-rate on optional |
| Validity | yes | type, range, regex, `accepted_values` |
| Uniqueness | yes | business keys, `(order_id, line_no)`, session key |
| Consistency | yes | `net = gross - discount + tax`; order total = sum(lines) |
| Referential integrity | yes | every fact `_sk` resolves (or is -1 with warn) |
| Timeliness | yes | `dbt source freshness`; no future `order_date` |
| Accuracy | yes | GMV vs source control totals (see 05) |

## Concrete rules (sample)

| Field / entity | Rule | Severity | On failure |
|----------------|------|----------|------------|
| `stg_oltp__orders.order_id` | not null, unique | error | fail run |
| `fct_order.currency` | `accepted_values` = seed `currency_list` | error | fail run |
| `fct_order.gmv` | `>= 0` unless `is_return` | error | quarantine row + count to threshold |
| `fct_order.order_date` | between 2015-01-01 and current_date | error | fail run |
| `fct_order_line` | sum(net) per order == `fct_order.net_amount` (± 0.01) | error | fail run |
| `dim_customer.email_hash` | matches `^[a-f0-9]{64}$` | error | fail run |
| `gold_pii.dim_customer_pii.email` | not present in `gold.*` (leak check) | error | fail run |
| `stg_shopify__orders` | `test = true` rows count == 0 after filter | warn | alert |
| `dim_fx_rate` | every currency in `fct_order` has a rate for `order_date` | error | carry-forward then warn |
| `fct_web_session.events` | `> 0` | warn | drop row |
| all `bronze` | `_run_id` not null | error | fail run |

## Thresholds

- **Fail the run if:** quarantined rows > **0.5%** of the batch for any entity,
  OR any `error`-severity generic test fails.
- **Warn if:** quarantined rows > **0.1%**, or `source freshness` in the warn
  band, or an Elementary anomaly (row count / null rate) fires.
- **Per-partition or whole-run:** evaluated per business date.

## Reporting & ownership

- **DQ report goes to:** Elementary dashboard (published to Databricks + a
  static site); daily digest to `#northwind-data` Slack; failures page
  Analytics Eng on-call via PagerDuty.
- **DQ score tracked?** yes - Elementary test pass-rate per model, 7-day trend;
  target >= 99.5%.
- **Owner of source-data fixes:** the source system owner in area 01; Analytics
  Eng owns rule tuning and quarantine triage.
