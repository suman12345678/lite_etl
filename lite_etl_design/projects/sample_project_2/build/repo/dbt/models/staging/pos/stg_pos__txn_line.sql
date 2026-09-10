-- stg_pos__txn_line
-- Implements: transformation-design.md s.2 (staging); requirements/03 cleansing
{{ config(materialized='view') }}

-- TODO: select from {{ source('pos', 'txn_line') }}; rename, cast, trim; drop is_deleted/_superseded/test
select 1 as _todo
