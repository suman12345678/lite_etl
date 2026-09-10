-- fct_order_line
-- Implements: data-entity-diagram.md (grain + keys); requirements/02 load pattern
{{ config(materialized='incremental', incremental_strategy='merge', unique_key=['order_id','line_no'], partition_by={'field':'order_date','data_type':'date'}) }}

-- TODO: build from int_* / snapshots; carry source_run_id + dbt_model_sha
select 1 as _todo
