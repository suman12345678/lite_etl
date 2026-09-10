-- dim_fx_rate
-- Implements: data-entity-diagram.md (grain + keys); requirements/02 load pattern
{{ config(materialized='table', unique_key=['rate_date','currency']) }}

-- TODO: build from int_* / snapshots; carry source_run_id + dbt_model_sha
select 1 as _todo
