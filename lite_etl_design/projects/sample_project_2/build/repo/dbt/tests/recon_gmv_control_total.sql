{{ config(tags=['recon', 'slice'], severity='error') }}
-- R2 (requirements/05): SUM(net_amount_usd) per channel in fct_order vs the control
-- total, fail if abs(delta) > recon.tolerance_pct of the control. Returns the
-- offending channel(s) (0 rows = PASS). Tolerance from config/defaults.yml -> var.

{% set tol = var('recon_tolerance_pct', 0.5) / 100.0 %}

with actual as (
    select channel, sum(net_amount_usd) as gmv_usd
    from {{ ref('fct_order') }}
    group by channel
),
expected as (
    select channel, expected_gmv_usd
    from {{ ref('control_totals') }}
)
select
    e.channel,
    e.expected_gmv_usd                                   as expected,
    coalesce(a.gmv_usd, 0)                               as actual,
    coalesce(a.gmv_usd, 0) - e.expected_gmv_usd          as delta,
    abs(coalesce(a.gmv_usd, 0) - e.expected_gmv_usd)
        / nullif(e.expected_gmv_usd, 0)                  as delta_frac
from expected e
left join actual a using (channel)
where abs(coalesce(a.gmv_usd, 0) - e.expected_gmv_usd) > {{ tol }} * abs(e.expected_gmv_usd)
