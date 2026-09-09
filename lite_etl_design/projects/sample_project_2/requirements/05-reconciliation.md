# 05 - Reconciliation

> DEMO - fictional. Proving a load before `gold` is published. Implemented as a
> blocking Dagster asset check backed by singular dbt tests + a Python
> manifest-compare step.

## Checks

| Check | Applies to | Tolerance | On failure |
|-------|-----------|-----------|------------|
| Row counts: source extracted == bronze landed == silver in + rejected + superseded | every source, per business date | exact | block publish |
| GMV control total: SUM(net_amount USD) per channel per date, `gold.fct_order` vs source-of-truth | web (Shopify payouts), store (POS totals file), wholesale (SFDC) | ± 0.5% | block publish |
| Refund balancing: SUM(refunds) <= SUM(order net) per customer per period; every refund links to an order | `fct_refund` vs `fct_order` | exact linkage; amount ± 0.01 | block publish |
| Order = sum of lines | `fct_order` vs `fct_order_line` | ± 0.01 | block publish |
| FX coverage | every currency/date in facts has a `dim_fx_rate` row | exact | block publish (carry-forward first) |
| Duplicate check | no unexpected dupes on `order_id`, `(order_id,line_no)`, `refund_id`, `(session_id,session_date)` | exact | block publish |
| Distribution drift | daily GMV, order count, AOV vs 28-day baseline | ± 30% -> warn; ± 60% -> block | alert / block |
| PII leak check | no raw email/phone/name in any `gold.*` object | exact | block publish |

## Gate behaviour

- A hard failure **blocks `gold` publish** - the Dagster `reconcile` asset check
  fails, downstream `publish` + `catalog_register` assets do not materialise, the
  run exits non-zero, PagerDuty fires.
- No auto-retry of reconciliation itself; the pipeline may retry the *transform*
  once for transient compute errors before reconcile runs.
- A `_reconciliation.json` report (per check: expected, actual, delta, verdict)
  is written to `s3://northwind-<env>-lakehouse/_recon/dt=.../` and surfaced in
  Elementary.

## Authoritative control report

- **Web:** Shopify daily payout / order summary export (already in `bronze` from
  the Shopify extract) is the GMV source of truth for `web`.
- **Store:** POS vendor also drops a `pos/dt=.../store=<id>/totals.csv` - store
  daily totals, reconciled against summed line items.
- **Wholesale:** Salesforce closed-won opportunity amount.

## Granularity

- Per business date, per channel. Whole-dataset hash check weekly.
