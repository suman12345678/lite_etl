-- staging: raw.* -> stg_*  (snake_case, cast, dedupe, resolve merges, hash PII)
-- These bodies double as the dbt staging models. sha256() is a UDF registered by
-- run.py (warehouses have a native one).

drop table if exists stg_plans;
create table stg_plans as
select plan_code, monthly_price_usd, plan_tier, is_retired
from raw_plans;

drop table if exists stg_fx_rates;
create table stg_fx_rates as
select
    substr(rate_date, 1, 7) as rate_month,
    currency,
    rate_to_usd
from raw_fx_rates;

-- accounts: drop the merged-away rows, hash the email, drop company_name
drop table if exists stg_accounts;
create table stg_accounts as
select
    account_id,
    country,
    company_domain,
    sha256(lower(billing_email)) as email_sha256
from raw_accounts
where merged_into is null;

drop table if exists stg_subscriptions;
create table stg_subscriptions as
select subscription_id, account_id, plan_code, start_month, end_month
from raw_subscriptions;

-- invoices: dedupe on invoice_id (keep newest updated_at) and remap merged account ids
drop table if exists stg_invoices;
create table stg_invoices as
with merge_map as (
    select account_id as old_id, merged_into as new_id
    from raw_accounts
    where merged_into is not null
),
ranked as (
    select
        i.invoice_id,
        coalesce(mm.new_id, i.account_id) as account_id,
        i.plan_code,
        i.invoice_month,
        i.currency,
        i.amount_local,
        i.status,
        row_number() over (partition by i.invoice_id order by i.updated_at desc) as rn
    from raw_invoices i
    left join merge_map mm on mm.old_id = i.account_id
)
select invoice_id, account_id, plan_code, invoice_month, currency, amount_local, status
from ranked
where rn = 1;
