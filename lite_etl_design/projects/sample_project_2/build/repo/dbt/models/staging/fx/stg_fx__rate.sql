-- stg_fx__rate
-- Implements: transformation-design.md s.2 (staging); requirements/03 cleansing
{{ config(materialized='view') }}

-- TODO: select from {{ source('fx', 'rate') }}; rename, cast, trim; drop is_deleted/_superseded/test
select 1 as _todo
