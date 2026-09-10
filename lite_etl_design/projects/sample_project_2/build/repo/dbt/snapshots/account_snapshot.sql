{% snapshot account_snapshot %}
{{ config(
    target_schema='silver',
    unique_key='account_bk',
    strategy='timestamp',
    updated_at='SystemModstamp',
) }}
-- Implements: transformation-design.md s.5 (SCD2)
-- TODO: select the account business key + tracked columns from int_account__resolved / stg_*
select 1 as _todo
{% endsnapshot %}
