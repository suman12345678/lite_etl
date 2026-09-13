-- Account x month spine, sum(prorated monthly_price_usd) over every subscription
-- active that month (Transforms: "MRR per account-month = active subscriptions x
-- dim_plan.monthly_price_usd, prorated for mid-period plan changes").
-- Same logic as demo/sql/20_marts.sql.

with accts as (
    select distinct account_id from {{ ref('stg_billing__subscriptions') }}
),
months(month) as (
    values ('2026-04'), ('2026-05'), ('2026-06'), ('2026-07')
),
grid as (
    select a.account_id, m.month from accts a cross join months m
),
sub_mrr as (
    select
        d.account_id,
        d.month,
        sum(round(p.monthly_price_usd * cast(d.overlap_days as double) / d.days_in_month, 2)) as mrr_usd
    from {{ ref('int_subscription_days') }} d
    join {{ ref('stg_ref__plans') }} p on p.plan_code = d.plan_code
    group by d.account_id, d.month
)
select
    g.account_id,
    g.month,
    coalesce(s.mrr_usd, 0) as mrr_usd
from grid g
left join sub_mrr s on s.account_id = g.account_id and s.month = g.month
