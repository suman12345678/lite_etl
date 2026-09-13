-- fct_order_line
-- Implements: data-entity-diagram.md (order-line grain); requirements/02.
-- Lines for published orders only, converted to USD via the order's currency.
{{ config(
    materialized='incremental',
    incremental_strategy='merge',
    unique_key=['order_id', 'line_no'],
    tags=['slice']
) }}
-- prod (dbt-databricks): also partition_by order_date - see transformation-design.md s.2

select
    l.order_id,
    l.line_no,
    l.product_id,
    l.quantity,
    l.net_amount,
    {{ to_usd('l.net_amount', 'o.currency', 'o.order_date') }} as net_amount_usd,
    o.order_date,
    o._run_id as source_run_id
from {{ ref('stg_oltp__order_lines') }} l
join {{ ref('stg_oltp__orders') }} o using (order_id)
where l.order_id in (select order_id from {{ ref('fct_order') }})

{% if is_incremental() %}
  and o.order_date >= (select coalesce(max(order_date), '1900-01-01') from {{ this }})
{% endif %}
