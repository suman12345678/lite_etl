-- grain: one row per plan_code. Same as demo/sql/20_marts.sql.

select
    plan_code,
    monthly_price_usd,
    plan_tier,
    is_retired
from {{ ref('stg_ref__plans') }}
