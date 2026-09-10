-- marts: stg_* -> dim_account, dim_plan, fct_invoice, fct_mrr_movement (+ mrr helpers)
-- These bodies double as the dbt marts models.

drop table if exists dim_plan;
create table dim_plan as
select plan_code, monthly_price_usd, plan_tier, is_retired
from stg_plans;

drop table if exists dim_account;
create table dim_account as
select account_id, country, company_domain, email_sha256
from stg_accounts;

-- fct_invoice: FX carry-forward (latest rate on or before invoice_month), USD,
-- recognized revenue = paid invoices only.
drop table if exists fct_invoice;
create table fct_invoice as
with with_rate as (
    select
        i.*,
        (
            select f.rate_to_usd
            from stg_fx_rates f
            where f.currency = i.currency
              and f.rate_month <= i.invoice_month
            order by f.rate_month desc
            limit 1
        ) as rate_to_usd
    from stg_invoices i
)
select
    invoice_id,
    account_id,
    plan_code,
    invoice_month,
    currency,
    amount_local,
    rate_to_usd,
    round(amount_local * rate_to_usd, 2) as amount_usd,
    case when status = 'paid'
         then round(amount_local * rate_to_usd, 2) else 0 end as recognized_revenue_usd,
    status
from with_rate;

-- month spine x every account that ever had a subscription
drop table if exists mrr_by_month;
create table mrr_by_month as
with months(m) as (
    values ('2026-04'), ('2026-05'), ('2026-06'), ('2026-07')
),
accts as (
    select distinct account_id from stg_subscriptions
),
grid as (
    select a.account_id, m.m from accts a cross join months m
)
select
    g.account_id,
    g.m as month,
    coalesce(sum(p.monthly_price_usd), 0) as mrr_usd
from grid g
left join stg_subscriptions s
    on s.account_id = g.account_id
   and s.start_month <= g.m
   and (s.end_month is null or g.m <= s.end_month)
left join dim_plan p on p.plan_code = s.plan_code
group by g.account_id, g.m;

-- classify each account-month MRR change
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
    from mrr_by_month
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
-- reflects the current contents of fct_mrr_movement)
drop view if exists mrr_recon;
create view mrr_recon as
with cur as (select max(month) as m from mrr_by_month),
prv as (select max(month) as m from mrr_by_month where month < (select m from cur))
select
    (select m from cur)                                                    as month,
    (select coalesce(sum(mrr_usd), 0) from mrr_by_month where month = (select m from prv)) as opening_mrr,
    (select coalesce(sum(mrr_usd), 0) from mrr_by_month where month = (select m from cur)) as closing_mrr,
    (select coalesce(sum(movement_amount), 0) from fct_mrr_movement where month = (select m from cur)) as movement_sum;
