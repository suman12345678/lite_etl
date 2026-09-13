-- grain: one row per invoice_id, money in USD.
-- FX carry-forward: most recent rate_date on or before invoice_date, per currency
-- (Transforms: join ref.fx_rates on (currency, invoice_date); carry forward on a
-- gap). recognized_revenue_usd = paid invoices only. Same as demo/sql/20_marts.sql.

with invoices as (
    select * from {{ ref('stg_billing__invoices') }}
),
fx as (
    select * from {{ ref('stg_ref__fx_rates') }}
),
with_rate as (
    select
        i.*,
        (
            select f.rate_to_usd
            from fx f
            where f.currency = i.currency
              and f.rate_date <= i.invoice_date
            order by f.rate_date desc
            limit 1
        ) as rate_to_usd
    from invoices i
)
select
    invoice_id,
    account_id,
    plan_code,
    invoice_date,
    invoice_month,
    currency,
    amount_local,
    rate_to_usd,
    round(amount_local * rate_to_usd, 2) as amount_usd,
    case when status = 'paid'
         then round(amount_local * rate_to_usd, 2) else 0 end as recognized_revenue_usd,
    status
from with_rate
