-- Drop test rows; hash PII at the staging boundary (raw email never goes downstream).
-- Same logic as demo/sql/10_staging.sql.

with source as (
    select * from {{ source('raw', 'raw_customers') }}
)
select
    customer_id,
    full_name,
    country,
    {{ to_sha256("lower(email)") }} as email_sha256
from source
where lower(email) not like '%@example.test'
