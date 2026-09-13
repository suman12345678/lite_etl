-- dim_customer
-- Implements: data-entity-diagram.md (customer dim); ADR-006 - gold carries only
-- the hashed email + non-identifying attrs, real PII lives in gold_pii.dim_customer_pii.
{{ config(materialized='table', unique_key='customer_sk', tags=['slice']) }}

select
    {{ surrogate_key(['customer_id']) }} as customer_sk,
    customer_id,
    email_hash,
    country,
    _run_id as source_run_id
from {{ ref('stg_oltp__customers') }}
