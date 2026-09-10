-- fct_refund
-- Implements: data-entity-diagram.md (grain + keys); requirements/02 load pattern
{{ config(materialized='incremental', incremental_strategy='merge', unique_key='refund_id', partition_by={'field':'refund_date','data_type':'date'}) }}

-- TODO: build from int_* / snapshots; carry source_run_id + dbt_model_sha
select 1 as _todo
