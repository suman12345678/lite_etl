-- reject__fct_order
-- DQ rule DQ03 (requirements/04, hardening/dq-behaviour-matrix.md): `gmv >= 0 unless
-- is_return`. Offending orders land here with a reason_code and are excluded from
-- fct_order - the quarantine mechanism. An empty table == clean day.
{{ config(materialized='table', schema='silver', tags=['slice', 'dq']) }}

select
    order_id,
    customer_id,
    currency,
    net_amount,
    net_amount_usd,
    order_date,
    'neg_gmv_non_return'                as reason_code,
    'DQ03'                              as _dq_rule,
    _run_id                            as _run_id,
    current_timestamp                  as _dq_ts
from {{ ref('int_sales__orders_usd') }}
where net_amount_usd < 0
  and not is_return
