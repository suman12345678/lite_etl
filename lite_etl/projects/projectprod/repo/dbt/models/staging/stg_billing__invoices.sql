-- Dedupe on invoice_id (keep newest updated_at, per Sources: webhook retries
-- re-send the same invoice) + remap merged account ids (old account_id -> the
-- surviving id, resolved before any aggregation downstream).
-- Same logic as demo/sql/10_staging.sql.

with source as (
    select * from {{ source('raw', 'billing_invoices') }}
),
merge_map as (
    select account_id as old_id, merged_into as new_id
    from {{ source('raw', 'crm_accounts') }}
    where merged_into is not null
),
ranked as (
    select
        i.invoice_id,
        coalesce(mm.new_id, i.account_id) as account_id,
        i.plan_code,
        i.invoice_date,
        substr(cast(i.invoice_date as varchar), 1, 7) as invoice_month,
        upper(i.currency) as currency,
        i.amount_local,
        i.status,
        row_number() over (partition by i.invoice_id order by i.updated_at desc) as rn
    from source i
    left join merge_map mm on mm.old_id = i.account_id
)
select invoice_id, account_id, plan_code, invoice_date, invoice_month, currency, amount_local, status
from ranked
where rn = 1
