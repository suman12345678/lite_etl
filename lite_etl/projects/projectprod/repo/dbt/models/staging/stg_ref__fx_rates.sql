-- Pass-through, one row per currency per day (grain per Sources: ref.fx_rates).
-- Gaps (weekends/holidays) are left as gaps here -- carry-forward is applied at
-- the join in fct_invoice, not here. Same logic as demo/sql/10_staging.sql.

select
    rate_date,
    upper(currency) as currency,
    rate_to_usd
from {{ source('raw', 'ref_fx_rates') }}
