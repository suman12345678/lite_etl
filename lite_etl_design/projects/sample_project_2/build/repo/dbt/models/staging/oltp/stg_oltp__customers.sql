-- stg_oltp__customers
-- Implements: transformation-design.md s.2 (staging); requirements/03 cleansing;
--             requirements/08 - hash email in silver, never carry raw PII forward.
{{ config(materialized='view', tags=['slice']) }}

select
    cast(customer_id as integer)                                    as customer_id,
    lower(trim(email))                                              as email_clean,
    sha256(lower(trim(email)) || '||' || '{{ var("pii_salt", "demo-salt") }}') as email_hash,
    upper(country)                                                  as country,
    cast(updated_at as timestamp)                                   as updated_at,
    _run_id
from {{ source('oltp', 'customers') }}
where not is_deleted                       -- soft-delete excluded (fixtures-catalog: soft_delete)
