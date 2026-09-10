-- Derive rate_month from the rate date. Same logic as demo/sql/10_staging.sql.

select
    substr(cast(rate_date as varchar), 1, 7) as rate_month,
    currency,
    rate_to_usd
from {{ source('raw', 'raw_fx_rates') }}
