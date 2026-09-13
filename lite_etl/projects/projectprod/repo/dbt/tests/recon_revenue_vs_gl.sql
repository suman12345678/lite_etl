-- Reconciliation gate (mirrors rules.yml: revenue_vs_finance_gl).
-- Fails - and blocks the publish - when current-month recognised revenue drifts
-- > 0.5% from the finance GL control total. 0 rows = pass.

with pipeline as (
    select coalesce(sum(recognized_revenue_usd), 0) as actual_usd
    from {{ ref('fct_invoice') }}
    where invoice_month = (select max(invoice_month) from {{ ref('fct_invoice') }})
),
control as (
    select expected_value as expected_usd
    from {{ ref('control_totals') }}
    where metric = 'recognized_revenue_usd_current_month'
)
select
    p.actual_usd,
    c.expected_usd,
    abs(p.actual_usd - c.expected_usd) / c.expected_usd * 100 as diff_pct
from pipeline p
cross join control c
where abs(p.actual_usd - c.expected_usd) / c.expected_usd * 100 > 0.5
