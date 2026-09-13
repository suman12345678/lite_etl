-- intermediate + marts: stg_* -> dim_account, dim_plan, fct_invoice, fct_mrr_movement
-- These bodies double as the dbt intermediate/marts models (dbt/models/intermediate/,
-- dbt/models/marts/). SQLite scalar max(a,b)/min(a,b) (2+ args) == greatest()/least().

-- ---------------------------------------------------------------------------
-- dims
-- ---------------------------------------------------------------------------
drop table if exists dim_plan;
create table dim_plan as
select plan_code, monthly_price_usd, plan_tier, is_retired
from stg_ref_plans;

drop table if exists dim_account;
create table dim_account as
select account_id, country, company_domain, email_sha256
from stg_crm_accounts;

-- ---------------------------------------------------------------------------
-- fct_invoice: FX carry-forward (most recent rate_date on or before invoice_date,
-- per currency), USD amount, recognized revenue = paid invoices only.
-- ---------------------------------------------------------------------------
drop table if exists fct_invoice;
create table fct_invoice as
with with_rate as (
    select
        i.*,
        (
            select f.rate_to_usd
            from stg_ref_fx_rates f
            where f.currency = i.currency
              and f.rate_date <= i.invoice_date
            order by f.rate_date desc
            limit 1
        ) as rate_to_usd
    from stg_billing_invoices i
)
select
    invoice_id,
    account_id,
    plan_code,
    invoice_date,
    invoice_month,
    currency,
    amount_local,
    rate_to_usd,
    round(amount_local * rate_to_usd, 2) as amount_usd,
    case when status = 'paid'
         then round(amount_local * rate_to_usd, 2) else 0 end as recognized_revenue_usd,
    status
from with_rate;

-- ---------------------------------------------------------------------------
-- int_subscription_days: per subscription x calendar month, how many days of that
-- month the subscription was active (proration for mid-period plan changes). The
-- demo fixture keeps every start/end on a month boundary, so overlap_days always
-- equals days_in_month here -- the formula itself handles a genuine partial month.
-- ---------------------------------------------------------------------------
drop table if exists int_subscription_days;
create table int_subscription_days as
with months(month, month_start, month_end_excl) as (
    values
        ('2026-04', '2026-04-01', '2026-05-01'),
        ('2026-05', '2026-05-01', '2026-06-01'),
        ('2026-06', '2026-06-01', '2026-07-01'),
        ('2026-07', '2026-07-01', '2026-08-01')
),
bounds as (
    select
        s.subscription_id,
        s.account_id,
        s.plan_code,
        m.month,
        m.month_start,
        m.month_end_excl,
        s.start_date as sub_start,
        coalesce(date(s.end_date, '+1 day'), '9999-12-31') as sub_end_excl
    from stg_billing_subscriptions s
    cross join months m
),
overlap as (
    select
        *,
        max(month_start, sub_start) as ov_start,
        min(month_end_excl, sub_end_excl) as ov_end_excl
    from bounds
)
select
    subscription_id,
    account_id,
    plan_code,
    month,
    julianday(ov_end_excl) - julianday(ov_start) as overlap_days,
    julianday(month_end_excl) - julianday(month_start) as days_in_month
from overlap
where ov_end_excl > ov_start;

-- ---------------------------------------------------------------------------
-- int_mrr_by_month: account x month spine, sum(prorated monthly_price_usd) over
-- every subscription active that month.
-- ---------------------------------------------------------------------------
drop table if exists int_mrr_by_month;
create table int_mrr_by_month as
with accts as (
    select distinct account_id from stg_billing_subscriptions
),
months(month) as (
    values ('2026-04'), ('2026-05'), ('2026-06'), ('2026-07')
),
grid as (
    select a.account_id, m.month from accts a cross join months m
),
sub_mrr as (
    select
        d.account_id,
        d.month,
        sum(round(p.monthly_price_usd * d.overlap_days / d.days_in_month, 2)) as mrr_usd
    from int_subscription_days d
    join stg_ref_plans p on p.plan_code = d.plan_code
    group by d.account_id, d.month
)
select
    g.account_id,
    g.month,
    coalesce(s.mrr_usd, 0) as mrr_usd
from grid g
left join sub_mrr s on s.account_id = g.account_id and s.month = g.month;

-- ---------------------------------------------------------------------------
-- fct_mrr_movement: classify each account-month MRR change vs the prior month
-- into new / expansion / contraction / churn / reactivation.
-- ---------------------------------------------------------------------------
drop table if exists fct_mrr_movement;
create table fct_mrr_movement as
with w as (
    select
        account_id, month, mrr_usd,
        lag(mrr_usd) over (partition by account_id order by month) as prev_mrr,
        max(mrr_usd) over (
            partition by account_id order by month
            rows between unbounded preceding and 1 preceding
        ) as max_prev_mrr
    from int_mrr_by_month
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
  and round(mrr_usd - coalesce(prev_mrr, 0), 2) <> 0;

-- one-row reconciliation helper for the current month (a view, so it always
-- reflects the current contents of fct_mrr_movement, e.g. after the fail
-- scenario deletes churn rows).
drop view if exists mrr_recon;
create view mrr_recon as
with cur as (select max(month) as m from int_mrr_by_month),
prv as (select max(month) as m from int_mrr_by_month where month < (select m from cur))
select
    (select m from cur)                                                        as month,
    (select coalesce(sum(mrr_usd), 0) from int_mrr_by_month where month = (select m from prv)) as opening_mrr,
    (select coalesce(sum(mrr_usd), 0) from int_mrr_by_month where month = (select m from cur)) as closing_mrr,
    (select coalesce(sum(movement_amount), 0) from fct_mrr_movement where month = (select m from cur)) as movement_sum;
