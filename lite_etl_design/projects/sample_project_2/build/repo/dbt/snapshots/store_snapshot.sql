{% snapshot store_snapshot %}
{{ config(
    target_schema='silver',
    unique_key='store_bk',
    strategy='check',
    updated_at='updated_at',
) }}
-- Implements: transformation-design.md s.5 (SCD2)
-- TODO: select the store business key + tracked columns from int_store__resolved / stg_*
select 1 as _todo
{% endsnapshot %}
