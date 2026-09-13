-- Pass-through, snake_case, one row per subscription. Mid-period plan changes
-- already arrive as a new subscription row (Sources: billing.subscriptions);
-- canceled_at can be backdated -- re-extracting incrementally by updated_at
-- (extract/billing.py) is what keeps end_date current, no special-casing needed
-- here. Same logic as demo/sql/10_staging.sql.

select
    subscription_id,
    account_id,
    plan_code,
    start_date,
    end_date
from {{ source('raw', 'billing_subscriptions') }}
