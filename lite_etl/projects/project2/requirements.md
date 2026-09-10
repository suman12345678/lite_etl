# Requirements brief — project2  (subscription revenue analytics)

Raw brief for the `/etl-spec` interview. Not a spec — informal notes, with open
questions left open. Run `/etl-spec project2` to turn this into `spec.md`.

---

## One-line goal
Nightly pipeline that turns raw billing + CRM data into a trusted `fct_invoice` +
`dim_account` + an MRR movement table, gated by data-quality and finance
reconciliation checks before anything is published.

## Engine
- Local demo: DuckDB (or stdlib SQLite) — must run with no cloud account.
- Prod: not decided — Snowflake or Databricks. Pipeline must not care; pick at the infra layer.

## Sources
| name | kind | grain | load | quirks |
|------|------|-------|------|--------|
| billing.invoices | REST API (Stripe-like) | one row per invoice | incremental by `updated_at` | webhook retries send the same invoice twice; amounts in customer currency; `status` in {draft, open, paid, void, uncollectible} |
| billing.subscriptions | REST API | one row per subscription | incremental | plan changes mid-period → proration lines; `canceled_at` can be backdated |
| crm.accounts | warehouse table (Postgres) | one row per account | full snapshot daily | contains PII (`billing_email`, `company_name`); account can be merged (old id points to new id) |
| ref.plans | s3 CSV, hand-maintained | one row per plan code | full | `monthly_price_usd`, `plan_tier`; occasionally a plan code is retired |
| ref.fx_rates | s3 CSV, daily | one row per currency per day | full | weekend / holiday gaps → carry forward last known rate |

## Target
- zones: raw → staging → marts
- model (grain in brackets):
  - `dim_account` [one row per surviving account_id; merged ids resolved; PII hashed]
  - `dim_plan` [one row per plan_code]
  - `fct_invoice` [one row per invoice_id; amounts in USD; recognized revenue split out]
  - `fct_mrr_movement` [one row per account per month per movement type: new / expansion / contraction / churn / reactivation]
- keys: account_id, plan_code, invoice_id

## Transforms (rough)
- dedupe invoices on `invoice_id`, keep latest `updated_at`
- resolve merged accounts: map old account_id → surviving id before aggregating
- currency → USD using `ref.fx_rates` on the invoice date; missing rate → carry forward
- `recognized_revenue_usd` = paid invoice amount for the period; exclude draft/void/uncollectible
- MRR per account-month from active subscriptions × plan price (prorated for mid-period changes)
- MRR movement = classify each account-month delta vs prior month
- hash `billing_email` and drop `company_name` free-text before marts (keep only `company_domain`)

## Rules (data quality + reconciliation — will become rules.yml)
- quality: `fct_invoice.invoice_id` not null                         on_fail: fail
- quality: `fct_invoice.amount_usd` >= 0                              on_fail: quarantine
- quality: `fct_invoice.status` in the known enum                     on_fail: quarantine
- quality: no marts column contains a raw email (`'%@%'`)             on_fail: fail
- quality: every `fct_invoice.plan_code` exists in `dim_plan`         on_fail: warn
- reconcile: `sum(recognized_revenue_usd)` for the month vs finance GL control total   tolerance 0.5%   on_fail: block
- reconcile: closing MRR == opening MRR + new + expansion − contraction − churn + reactivation   tolerance 0.1%   on_fail: block

## Schedule
- cadence: daily 02:00 after the FX file and the CRM snapshot land; deadline 04:00
- also an hourly lightweight run to pull new invoices (no publish, just land raw)
- backfill: re-run a month by date range; publish is idempotent replace per `month`

## Non-functional
- volume: demo ~500 invoices; prod ~2M invoices/month, ~40 GB total, growing ~5%/month
- latency: curated tables ready < 30 min after inputs land
- cost: demo $0; prod warehouse ceiling to be set by finance
- pii: `billing_email` → sha256 at the staging boundary; raw email/company name never reach staging or marts
- envs: dev, prod

## Open questions
- Prod engine: Snowflake vs Databricks — decide at infra, not in the models.
- Proration: exact rule for mid-month plan downgrades (finance to confirm).
- Do we need multi-currency reporting output, or is USD-only fine for v1?
- Late-arriving invoices past month close — restate the closed month, or book to current month?
