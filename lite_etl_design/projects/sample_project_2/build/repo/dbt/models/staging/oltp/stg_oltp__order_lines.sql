-- stg_oltp__order_lines
-- Implements: transformation-design.md s.2 (staging); requirements/03 cleansing.
{{ config(materialized='view', tags=['slice']) }}

select
    cast(order_id as integer)         as order_id,
    cast(line_no as integer)          as line_no,
    cast(product_id as integer)       as product_id,
    cast(quantity as integer)         as quantity,
    cast(net_amount as decimal(12,2)) as net_amount,
    _run_id
from {{ source('oltp', 'order_lines') }}
