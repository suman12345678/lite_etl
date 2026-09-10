-- grain: one row per customer_id. No raw PII. Same logic as demo/sql/20_marts.sql.

select
    customer_id,
    full_name,
    country,
    email_sha256
from {{ ref('stg_customers') }}
