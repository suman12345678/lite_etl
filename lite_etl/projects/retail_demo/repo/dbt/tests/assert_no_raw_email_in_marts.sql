-- PII guard (mirrors rules.yml: no_raw_email_in_marts).
-- Any marts row where the hashed column still looks like an email address = fail.

select customer_id, email_sha256
from {{ ref('dim_customer') }}
where email_sha256 like '%@%'
