-- grain: one row per account_id per month per movement type (Target: new /
-- expansion / contraction / churn / reactivation). Classifies each account-month
-- MRR change vs the prior month. Real body -- same logic as demo/sql/20_marts.sql
-- (this used to be the etl-build "next slice"; projectprod ships it complete):
--   1. int_subscription_days  : per-subscription-per-month day overlap (proration)
--   2. int_mrr_by_month       : account x month spine, sum(prorated mrr_usd)
--   3. this model             : lag() + max() over preceding rows -> classify
-- The reconciliation identity (closing == opening + sum(movement_amount), i.e.
-- rules.yml: mrr_movement_identity) is verified by dbt/tests/recon_mrr_identity.sql.

with w as (
    select
        account_id, month, mrr_usd,
        lag(mrr_usd) over (partition by account_id order by month) as prev_mrr,
        max(mrr_usd) over (
            partition by account_id order by month
            rows between unbounded preceding and 1 preceding
        ) as max_prev_mrr
    from {{ ref('int_mrr_by_month') }}
)
select
    account_id,
    month,
    coalesce(prev_mrr, 0) as opening_mrr,
    mrr_usd as closing_mrr,
    round(mrr_usd - coalesce(prev_mrr, 0), 2) as movement_amount,
    case
        when coalesce(prev_mrr, 0) = 0 and mrr_usd > 0 and coalesce(max_prev_mrr, 0) > 0 then 'reactivation'
        when coalesce(prev_mrr, 0) = 0 and mrr_usd > 0 then 'new'
        when coalesce(prev_mrr, 0) > 0 and mrr_usd = 0 then 'churn'
        when mrr_usd > coalesce(prev_mrr, 0) then 'expansion'
        when mrr_usd < coalesce(prev_mrr, 0) then 'contraction'
        else 'none'
    end as movement_type
from w
where month > '2026-04'
  and round(mrr_usd - coalesce(prev_mrr, 0), 2) <> 0
