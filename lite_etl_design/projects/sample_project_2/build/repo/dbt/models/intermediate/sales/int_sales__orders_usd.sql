-- int_sales__orders_usd
-- Implements: transformation-design.md s.2 (intermediate); requirements/03 - convert
-- each order's net_amount to the USD reporting currency. Single channel ('direct')
-- in the walking-skeleton slice; the full build unions web / store / wholesale here.
{{ config(materialized='ephemeral', tags=['slice']) }}

select
    o.order_id,
    o.customer_id,
    o.currency,
    o.net_amount,
    o.is_return,
    o.order_date,
    'direct'                                              as channel,
    {{ to_usd('o.net_amount', 'o.currency', 'o.order_date') }} as net_amount_usd,
    o._run_id
from {{ ref('stg_oltp__orders') }} o
