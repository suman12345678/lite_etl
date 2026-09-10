-- fct_web_session
-- Implements: data-entity-diagram.md (grain + keys); requirements/02 load pattern
{{ config(materialized='incremental', incremental_strategy='delete+insert', unique_key=['session_id','session_date'], partition_by={'field':'session_date','data_type':'date'}) }}

-- TODO: build from int_* / snapshots; carry source_run_id + dbt_model_sha
select 1 as _todo
