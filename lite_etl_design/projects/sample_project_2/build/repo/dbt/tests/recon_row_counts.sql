{{ config(tags=['recon', 'slice'], severity='error') }}
-- R1 (requirements/05): landed orders == published + quarantined + soft-deleted.
-- Returns one row if the identity is broken (0 rows = PASS).

with landed as (
    select count(*) as n from {{ source('oltp', 'orders') }}
),
deleted as (
    select count(*) as n from {{ source('oltp', 'orders') }} where is_deleted
),
published as (
    select count(*) as n from {{ ref('fct_order') }}
),
quarantined as (
    select count(*) as n from {{ ref('reject__fct_order') }}
)
select
    landed.n      as landed,
    published.n   as published,
    quarantined.n as quarantined,
    deleted.n     as soft_deleted
from landed, deleted, published, quarantined
where landed.n <> published.n + quarantined.n + deleted.n
