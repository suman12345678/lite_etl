-- stg_oltp__orders
-- Implements: transformation-design.md s.2 (staging); requirements/03 cleansing.
{{ config(materialized='view', tags=['slice']) }}

select
    cast(order_id as integer)         as order_id,
    cast(customer_id as integer)      as customer_id,
    upper(currency)                   as currency,
    cast(net_amount as decimal(12,2)) as net_amount,
    cast(is_return as boolean)        as is_return,
    cast(order_date as date)          as order_date,
    cast(updated_at as timestamp)     as updated_at,
    _run_id
from {{ source('oltp', 'orders') }}
where not is_deleted
