-- Reconciliation gate (mirrors rules.yml: web_net_usd_vs_finance).
-- Fails - and blocks the publish - when web net_usd drifts > 0.5% from the
-- finance control total. Returns the breaching row(s); 0 rows = pass.

with pipeline as (
    select sum(net_usd) as actual_net_usd
    from {{ ref('fct_order') }}
    where channel = 'web'
),
control as (
    select expected_net_usd
    from {{ ref('control_totals') }}
    where channel = 'web'
)
select
    p.actual_net_usd,
    c.expected_net_usd,
    abs(p.actual_net_usd - c.expected_net_usd) / c.expected_net_usd * 100 as diff_pct
from pipeline p
cross join control c
where abs(p.actual_net_usd - c.expected_net_usd) / c.expected_net_usd * 100 > 0.5
