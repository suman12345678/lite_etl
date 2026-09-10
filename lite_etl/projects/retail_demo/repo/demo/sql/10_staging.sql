-- staging: raw.* -> stg_*  (snake_case, cast dates, drop test rows, hash PII, dedupe)
-- This is the body of the dbt staging models in dbt/models/staging/. sha256() is a
-- UDF registered by run.py (the warehouse has a native one).

drop table if exists stg_customers;
create table stg_customers as
select
    customer_id,
    full_name,
    country,
    sha256(lower(email))         as email_sha256      -- raw email never leaves staging
from raw_customers
where lower(email) not like '%@example.test';         -- drop test rows

drop table if exists stg_fx_rates;
create table stg_fx_rates as
select
    date(rate_date)              as rate_date,
    currency,
    rate_to_usd
from raw_fx_rates;

-- dedupe orders on order_id, keep the row with the newest loaded_at
drop table if exists stg_orders;
create table stg_orders as
with ranked as (
    select
        order_id,
        customer_id,
        channel,
        currency,
        amount_local,
        date(order_ts)          as order_date,
        row_number() over (partition by order_id order by loaded_at desc) as rn
    from raw_orders
)
select order_id, customer_id, channel, currency, amount_local, order_date
from ranked
where rn = 1;
