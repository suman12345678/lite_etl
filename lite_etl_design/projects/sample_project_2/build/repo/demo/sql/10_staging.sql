-- Demo staging: bronze.* -> stg_* (the real pipeline does this in dbt/models/staging/).
-- Plain DuckDB SQL so `make demo` runs with no warehouse and no dbt.

create or replace table stg_oltp__customers as
select
    customer_id,
    lower(trim(email))                                as email_clean,
    sha256(lower(trim(email)) || '||{salt}')          as email_hash,   -- silver hashes PII (08 / ADR-006)
    country,
    updated_at
from bronze.oltp__customers
where not is_deleted;                                                  -- soft-delete excluded

create or replace table stg_oltp__orders as
select
    order_id,
    customer_id,
    upper(currency)                                   as currency,
    net_amount,
    is_return,
    order_date,
    updated_at
from bronze.oltp__orders
where not is_deleted;

create or replace table stg_oltp__order_lines as
select order_id, line_no, product_id, quantity, net_amount
from bronze.oltp__order_lines;

create or replace table stg_fx__rate as
select upper(currency) as currency, rate_per_usd, rate_date
from bronze.fx__rate;
