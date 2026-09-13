-- grain: one row per surviving account_id. No raw PII. Same as demo/sql/20_marts.sql.

select
    account_id,
    country,
    company_domain,
    email_sha256
from {{ ref('stg_crm__accounts') }}
