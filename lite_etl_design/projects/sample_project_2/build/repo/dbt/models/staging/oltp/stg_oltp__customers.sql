-- stg_oltp__customers
-- Implements: transformation-design.md s.2 (staging); requirements/03 cleansing
{{ config(materialized='view') }}

-- TODO: select from {{ source('oltp', 'customers') }}; rename, cast, trim; drop is_deleted/_superseded/test
select 1 as _todo
