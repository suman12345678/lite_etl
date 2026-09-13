-- Per subscription x calendar month: how many days of that month the
-- subscription was active (Transforms: MRR proration for mid-period plan
-- changes). Same logic as demo/sql/20_marts.sql, DuckDB/warehouse dialect
-- (date arithmetic + greatest/least/date_diff instead of SQLite's
-- julianday()/date()).

with months(month, month_start, month_end_excl) as (
    values
        ('2026-04', date '2026-04-01', date '2026-05-01'),
        ('2026-05', date '2026-05-01', date '2026-06-01'),
        ('2026-06', date '2026-06-01', date '2026-07-01'),
        ('2026-07', date '2026-07-01', date '2026-08-01')
),
bounds as (
    select
        s.subscription_id,
        s.account_id,
        s.plan_code,
        m.month,
        m.month_start,
        m.month_end_excl,
        cast(s.start_date as date) as sub_start,
        case when s.end_date is null then date '9999-12-31'
             else cast(s.end_date as date) + interval 1 day end as sub_end_excl
    from {{ ref('stg_billing__subscriptions') }} s
    cross join months m
),
overlap as (
    select
        *,
        greatest(month_start, sub_start) as ov_start,
        least(month_end_excl, sub_end_excl) as ov_end_excl
    from bounds
)
select
    subscription_id,
    account_id,
    plan_code,
    month,
    date_diff('day', ov_start, ov_end_excl) as overlap_days,
    date_diff('day', month_start, month_end_excl) as days_in_month
from overlap
where ov_end_excl > ov_start
