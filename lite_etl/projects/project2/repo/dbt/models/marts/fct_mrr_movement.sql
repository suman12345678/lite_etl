-- STUB. The real, tested body lives in demo/sql/20_marts.sql (mrr_by_month ->
-- lag() classification -> mrr_recon). Port it here as part of the next slice:
--   1. int_mrr_by_month  : account x month spine, sum(active subs x plan price)
--   2. this model        : lag() prev_mrr + max() over preceding rows -> classify
--                          new / expansion / contraction / churn / reactivation
--   3. a singular test    : closing MRR == opening MRR + sum(movement_amount)   (rules.yml: mrr_movement_identity)
-- TODO: implement; until then this returns an empty result with the right shape.

select
    cast(null as varchar)  as account_id,
    cast(null as varchar)  as month,
    cast(null as double)    as opening_mrr,
    cast(null as double)    as closing_mrr,
    cast(null as double)    as movement_amount,
    cast(null as varchar)  as movement_type
where 1 = 0
