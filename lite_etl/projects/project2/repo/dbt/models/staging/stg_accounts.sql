-- Drop merged-away rows; hash PII at the staging boundary; drop company_name.
-- Same logic as demo/sql/10_staging.sql.

with source as (
    select * from {{ source('raw', 'raw_accounts') }}
)
select
    account_id,
    country,
    company_domain,
    {{ to_sha256("lower(billing_email)") }} as email_sha256
from source
where merged_into is null
