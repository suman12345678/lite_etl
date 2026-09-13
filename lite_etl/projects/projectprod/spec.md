# Spec — projectprod

engine: duckdb | databricks | snowflake      <!-- duckdb = local demo; prod engine not yet chosen, see Open questions -->
owner: suman    date: 2026-09-13

<!-- Subscription revenue analytics. Drafted from requirements.md (same brief as project2). -->

## Sources
| name | kind | grain | load | quirks |
|------|------|-------|------|--------|
| billing.invoices | rest (Stripe-like API) | row (one per invoice) | incremental by `updated_at` | webhook retries re-send the same invoice; amount in customer currency; `status` in {draft, open, paid, void, uncollectible} |
| billing.subscriptions | rest (API) | row (one per subscription) | incremental | mid-period plan changes create proration lines; `canceled_at` can be backdated |
| crm.accounts | warehouse (Postgres) | row (one per account) | full snapshot daily | PII: `billing_email`, `company_name`; merged accounts — old `account_id` points to a surviving id |
| ref.plans | s3-file (CSV, hand-maintained) | row (one per plan code) | full | `monthly_price_usd`, `plan_tier`; plan codes are occasionally retired |
| ref.fx_rates | s3-file (CSV, daily) | row (one per currency per day) | full | weekend / holiday gaps → carry forward last known rate |

## Target
- zones: raw -> staging -> marts
- model:
  - `dim_account`        — grain: one row per surviving `account_id`; merged ids resolved; `billing_email` stored only as `email_sha256`; free-text `company_name` dropped (keep `company_domain`)
  - `dim_plan`           — grain: one row per `plan_code`
  - `fct_invoice`        — grain: one row per `invoice_id`; `amount_usd`; `recognized_revenue_usd` (paid invoices in period only)
  - `fct_mrr_movement`   — grain: one row per `account_id` per `month` per movement type (new / expansion / contraction / churn / reactivation)
- keys: `account_id` (dim_account), `plan_code` (dim_plan), `invoice_id` (fct_invoice)

## Transforms
- cast timestamps to date; rename all columns to snake_case
- dedupe `invoices` on `invoice_id`, keep the row with the latest `updated_at`
- resolve merged accounts: map old `account_id` → surviving id before any aggregation
- join `ref.fx_rates` on `(currency, invoice_date)`; if no rate that day, use the most recent prior rate (carry forward)
- `amount_usd = round(amount_local * rate_to_usd, 2)`
- `recognized_revenue_usd`: amount of `paid` invoices attributable to the period; exclude `draft` / `void` / `uncollectible`
- MRR per account-month = active subscriptions × `dim_plan.monthly_price_usd`, prorated for mid-period plan changes
- `fct_mrr_movement`: classify each account-month MRR delta vs the prior month into new / expansion / contraction / churn / reactivation
- hash `crm.accounts.billing_email` → `email_sha256` at the staging boundary; drop `company_name`, derive `company_domain`; raw email / company name never reach staging or marts

## Rules
<!-- these become repo/rules.yml -->
- quality: `fct_invoice.invoice_id` is not null                      on_fail: fail
- quality: `fct_invoice.amount_usd` >= 0                              on_fail: quarantine
- quality: `fct_invoice.status` in {draft, open, paid, void, uncollectible}   on_fail: quarantine
- quality: no marts column contains a raw email (`'%@%'`)            on_fail: fail
- quality: every `fct_invoice.plan_code` exists in `dim_plan`        on_fail: warn
- reconcile: `sum(recognized_revenue_usd)` for the month vs finance GL control total   tolerance 0.5%   on_fail: block
- reconcile: closing MRR vs `opening MRR + new + expansion - contraction - churn + reactivation`   tolerance 0.1%   on_fail: block

## Schedule
- cadence: daily 02:00, after the FX file and the CRM snapshot land; deadline 04:00.
  Plus an hourly lightweight run that only lands new invoices to raw (no transform, no publish).
- backfill: `--date-range <start> <end>` re-runs one month at a time; publish is idempotent replace per `month`

## Non-functional
- volume: demo ~500 invoices/run; prod ~2M invoices/month, ~40 GB total, growth ~5%/month   latency: curated tables ready < 30 min after inputs land   cost: demo $0; prod warehouse ceiling TBD (finance)
- pii: `billing_email` → sha256 at the staging boundary; `company_name` dropped (keep `company_domain`); raw values never land in staging or marts
- envs: dev, prod

## Open questions
- Prod engine is not chosen — Snowflake or Databricks. Pipeline is engine-agnostic (dbt models + `rules.yml` unchanged); decide at the Terraform `engine` variable.
- Proration: exact rule for mid-month plan downgrades — finance to confirm.
- Reporting currency: USD-only for v1, or is a multi-currency reporting output required?
- Late-arriving invoices after month close: restate the closed month, or book to the current month?
