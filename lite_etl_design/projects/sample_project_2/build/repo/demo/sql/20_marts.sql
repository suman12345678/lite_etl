-- Demo marts: stg_* -> int_* -> dim_* / fct_* + the DQ quarantine table.
-- The real pipeline does this in dbt/models/{intermediate,marts}/. Plain DuckDB SQL here.

create or replace table dim_fx_rate as
select currency, rate_per_usd, rate_date from stg_fx__rate;

-- gold-facing customer: surrogate key + hashed email only, never raw PII (DQ08)
create or replace table dim_customer as
select
    md5(cast(customer_id as varchar)) as customer_sk,
    customer_id,
    email_hash,
    country
from stg_oltp__customers;

-- orders converted to the USD reporting currency (int layer)
create or replace table int_orders_usd as
select
    o.order_id,
    o.customer_id,
    o.currency,
    o.net_amount,
    o.is_return,
    o.order_date,
    round(o.net_amount / f.rate_per_usd, 2) as net_amount_usd
from stg_oltp__orders o
left join dim_fx_rate f on f.currency = o.currency;

-- DQ rule DQ03: `gmv >= 0 unless is_return` -> quarantine the offenders.
-- This is the "data-quality catch + correction" mechanism: bad rows land here with a
-- reason_code and never reach gold; a fixed source re-run produces an empty table.
create or replace table reject__fct_order as
select
    order_id,
    customer_id,
    currency,
    net_amount,
    net_amount_usd,
    order_date,
    'neg_gmv_non_return'  as reason_code,
    '{run_id}'            as _run_id,
    'DQ03'               as _dq_rule,
    now()                as _dq_ts
from int_orders_usd
where net_amount_usd < 0 and not is_return;

-- fct_order: clean orders only (quarantined orders removed)
create or replace table fct_order as
select
    md5(cast(o.customer_id as varchar)) as customer_sk,
    o.order_id,
    o.customer_id,
    o.currency,
    o.net_amount,
    o.net_amount_usd,
    o.is_return,
    o.order_date,
    'direct'    as channel,
    '{run_id}'  as source_run_id
from int_orders_usd o
where o.order_id not in (select order_id from reject__fct_order);

-- fct_order_line: lines for published orders, converted to USD via the order's currency
create or replace table fct_order_line as
select
    l.order_id,
    l.line_no,
    l.product_id,
    l.quantity,
    l.net_amount,
    round(l.net_amount / f.rate_per_usd, 2) as net_amount_usd
from stg_oltp__order_lines l
join stg_oltp__orders o on o.order_id = l.order_id
left join dim_fx_rate f on f.currency = o.currency
where l.order_id in (select order_id from fct_order);
