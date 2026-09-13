-- fct_order
-- Implements: data-entity-diagram.md (order grain); requirements/02 load pattern.
-- Clean orders only - anything in reject__fct_order (DQ03) is held back.
{{ config(
    materialized='incremental',
    incremental_strategy='merge',
    unique_key=['order_id', 'channel'],
    tags=['slice']
) }}
-- prod (dbt-databricks): also partition_by order_date - see transformation-design.md s.2

select
    {{ surrogate_key(['o.customer_id']) }} as customer_sk,
    o.order_id,
    o.customer_id,
    o.currency,
    o.net_amount,
    o.net_amount_usd,
    o.is_return,
    o.order_date,
    o.channel,
    o._run_id as source_run_id
from {{ ref('int_sales__orders_usd') }} o
where o.order_id not in (select order_id from {{ ref('reject__fct_order') }})

{% if is_incremental() %}
  and o.order_date >= (select coalesce(max(order_date), '1900-01-01') from {{ this }})
{% endif %}
