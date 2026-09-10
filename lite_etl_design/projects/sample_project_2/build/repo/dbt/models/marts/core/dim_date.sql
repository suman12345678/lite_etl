-- dim_date
-- Implements: data-entity-diagram.md (grain + keys); requirements/02 load pattern
{{ config(materialized='table', unique_key='date_key') }}

-- TODO: build from int_* / snapshots; carry source_run_id + dbt_model_sha
select 1 as _todo
