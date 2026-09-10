-- {{ config(tags=['recon']) }}
-- SUM(net_amount_usd) per channel/date vs control total; fail if abs(delta) > 0.005 * control. requirements/05
-- TODO: return rows that VIOLATE the rule (0 rows = pass)
select 1 as _todo where false
