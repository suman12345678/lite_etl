{% snapshot product_snapshot %}
{{ config(
    target_schema='silver',
    unique_key='product_bk',
    strategy='timestamp',
    updated_at='updated_at',
) }}
-- Implements: transformation-design.md s.5 (SCD2)
-- TODO: select the product business key + tracked columns from int_product__resolved / stg_*
select 1 as _todo
{% endsnapshot %}
