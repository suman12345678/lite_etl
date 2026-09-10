-- Pass-through. Same logic as demo/sql/10_staging.sql.

select
    subscription_id,
    account_id,
    plan_code,
    start_month,
    end_month
from {{ source('raw', 'raw_subscriptions') }}
