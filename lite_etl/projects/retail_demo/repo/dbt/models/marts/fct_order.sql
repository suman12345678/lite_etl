-- grain: one row per order_id, money in USD.
-- FX carry-forward: use the most recent rate on or before order_date.
-- Same logic as demo/sql/20_marts.sql.

with orders as (
    select * from {{ ref('stg_orders') }}
),
fx as (
    select * from {{ ref('stg_fx_rates') }}
),
with_rate as (
    select
        o.*,
        (
            select f.rate_to_usd
            from fx f
            where f.currency = o.currency
              and f.rate_date <= o.order_date
            order by f.rate_date desc
            limit 1
        ) as rate_to_usd
    from orders o
)
select
    order_id,
    customer_id,
    channel,
    currency,
    order_date,
    amount_local,
    rate_to_usd,
    round(amount_local * rate_to_usd, 2) as net_usd
from with_rate
