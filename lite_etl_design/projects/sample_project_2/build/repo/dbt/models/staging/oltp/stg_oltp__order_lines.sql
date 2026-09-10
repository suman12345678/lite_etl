-- stg_oltp__order_lines
-- Implements: transformation-design.md s.2 (staging); requirements/03 cleansing
{{ config(materialized='view') }}

-- TODO: select from {{ source('oltp', 'order_lines') }}; rename, cast, trim; drop is_deleted/_superseded/test
select 1 as _todo
