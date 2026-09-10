-- marts: stg_* -> dim_customer, fct_order
-- Body of the dbt marts models in dbt/models/marts/.

drop table if exists dim_customer;
create table dim_customer as
select
    customer_id,
    full_name,
    country,
    email_sha256
from stg_customers;

-- fct_order: FX carry-forward join (most recent rate on or before order_date),
-- money converted to USD. Rows with no usable rate get net_usd = NULL and are
-- caught by the quality checks.
drop table if exists fct_order;
create table fct_order as
select
    o.order_id,
    o.customer_id,
    o.channel,
    o.currency,
    o.order_date,
    o.amount_local,
    (
        select fx.rate_to_usd
        from stg_fx_rates fx
        where fx.currency = o.currency
          and fx.rate_date <= o.order_date
        order by fx.rate_date desc
        limit 1
    )                                                         as rate_to_usd,
    round(
        o.amount_local * (
            select fx.rate_to_usd
            from stg_fx_rates fx
            where fx.currency = o.currency
              and fx.rate_date <= o.order_date
            order by fx.rate_date desc
            limit 1
        ), 2)                                                 as net_usd
from stg_orders o;
