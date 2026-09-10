-- stg_sfdc__contact
-- Implements: transformation-design.md s.2 (staging); requirements/03 cleansing
{{ config(materialized='view') }}

-- TODO: select from {{ source('sfdc', 'contact') }}; rename, cast, trim; drop is_deleted/_superseded/test
select 1 as _todo
