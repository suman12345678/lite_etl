-- dim_fx_rate
-- Implements: data-entity-diagram.md (fx dimension); requirements/03 currency conversion.
{{ config(materialized='table', unique_key=['rate_date', 'currency'], tags=['slice']) }}

select
    currency,
    rate_per_usd,
    rate_date,
    _run_id as source_run_id
from {{ ref('stg_fx__rate') }}
