-- Reconciliation gate (mirrors rules.yml: mrr_movement_identity).
-- closing MRR must equal opening MRR + new + expansion - contraction - churn +
-- reactivation, i.e. opening + sum(signed movement_amount) (movement_amount is
-- already signed: positive for new/expansion/reactivation, negative for
-- contraction/churn). Fails - and blocks the publish - when the two drift
-- > 0.1%. 0 rows = pass.

with cur as (
    select max(month) as m from {{ ref('int_mrr_by_month') }}
),
prv as (
    select max(month) as m from {{ ref('int_mrr_by_month') }} where month < (select m from cur)
),
recon as (
    select
        (select coalesce(sum(mrr_usd), 0) from {{ ref('int_mrr_by_month') }}
            where month = (select m from prv)) as opening_mrr,
        (select coalesce(sum(mrr_usd), 0) from {{ ref('int_mrr_by_month') }}
            where month = (select m from cur)) as closing_mrr,
        (select coalesce(sum(movement_amount), 0) from {{ ref('fct_mrr_movement') }}
            where month = (select m from cur)) as movement_sum
)
select
    opening_mrr,
    closing_mrr,
    movement_sum,
    opening_mrr + movement_sum as expected_closing_mrr,
    abs(closing_mrr - (opening_mrr + movement_sum))
        / case when (opening_mrr + movement_sum) = 0 then 1 else abs(opening_mrr + movement_sum) end
        * 100 as diff_pct
from recon
where abs(closing_mrr - (opening_mrr + movement_sum))
        / case when (opening_mrr + movement_sum) = 0 then 1 else abs(opening_mrr + movement_sum) end
        * 100 > 0.1
