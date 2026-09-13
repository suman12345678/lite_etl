{{ config(tags=['recon', 'slice'], severity='error') }}
-- R4 (requirements/04 consistency, requirements/05 check 4): fct_order.net_amount_usd
-- == SUM(fct_order_line.net_amount_usd) per order, within 0.01. Returns offenders.

select
    o.order_id,
    o.net_amount_usd                                   as order_usd,
    coalesce(sum(l.net_amount_usd), 0)                 as lines_usd,
    o.net_amount_usd - coalesce(sum(l.net_amount_usd), 0) as delta
from {{ ref('fct_order') }} o
left join {{ ref('fct_order_line') }} l on l.order_id = o.order_id
group by o.order_id, o.net_amount_usd
having abs(o.net_amount_usd - coalesce(sum(l.net_amount_usd), 0)) > 0.01
