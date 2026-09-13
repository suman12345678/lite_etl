-- stg_fx__rate
-- Implements: transformation-design.md s.2 (staging). One row per (currency, rate_date),
-- units of the currency per 1 USD (base = USD).
{{ config(materialized='view', tags=['slice']) }}

select
    upper(currency)                as currency,
    cast(rate_per_usd as double)   as rate_per_usd,
    cast(rate_date as date)        as rate_date,
    _run_id
from {{ source('fx', 'rate') }}
where rate_per_usd > 0
