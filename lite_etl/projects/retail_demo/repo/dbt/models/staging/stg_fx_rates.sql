-- Pass-through with a date cast. Same logic as demo/sql/10_staging.sql.

select
    cast(rate_date as date) as rate_date,
    currency,
    rate_to_usd
from {{ source('raw', 'raw_fx_rates') }}
