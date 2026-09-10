-- grain: one row per invoice_id, money in USD.
-- FX carry-forward: most recent rate on or before invoice_month.
-- recognized_revenue_usd = paid invoices only. Same as demo/sql/20_marts.sql.

with invoices as (
    select * from {{ ref('stg_invoices') }}
),
fx as (
    select * from {{ ref('stg_fx_rates') }}
),
with_rate as (
    select
        i.*,
        (
            select f.rate_to_usd
            from fx f
            where f.currency = i.currency
              and f.rate_month <= i.invoice_month
            order by f.rate_month desc
            limit 1
        ) as rate_to_usd
    from invoices i
)
select
    invoice_id,
    account_id,
    plan_code,
    invoice_month,
    currency,
    amount_local,
    rate_to_usd,
    round(amount_local * rate_to_usd, 2) as amount_usd,
    case when status = 'paid'
         then round(amount_local * rate_to_usd, 2) else 0 end as recognized_revenue_usd,
    status
from with_rate
