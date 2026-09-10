-- Pass-through. Same logic as demo/sql/10_staging.sql.

select
    plan_code,
    monthly_price_usd,
    plan_tier,
    is_retired
from {{ source('raw', 'raw_plans') }}
