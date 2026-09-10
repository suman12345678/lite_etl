-- Snake_case + cast date + dedupe on order_id (keep newest loaded_at).
-- Same logic as demo/sql/10_staging.sql.

with source as (
    select * from {{ source('raw', 'raw_orders') }}
),
ranked as (
    select
        order_id,
        customer_id,
        channel,
        currency,
        amount_local,
        cast(order_ts as date) as order_date,
        row_number() over (partition by order_id order by loaded_at desc) as rn
    from source
)
select
    order_id,
    customer_id,
    channel,
    currency,
    amount_local,
    order_date
from ranked
where rn = 1
