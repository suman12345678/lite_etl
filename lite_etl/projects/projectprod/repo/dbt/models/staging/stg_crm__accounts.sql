-- Drop merged-away rows; hash PII at the staging boundary; drop company_name,
-- keep company_domain (Non-functional: raw billing_email/company_name must never
-- reach staging or marts). Same logic as demo/sql/10_staging.sql.

with source as (
    select * from {{ source('raw', 'crm_accounts') }}
)
select
    account_id,
    country,
    company_domain,
    {{ to_sha256("lower(billing_email)") }} as email_sha256
from source
where merged_into is null
