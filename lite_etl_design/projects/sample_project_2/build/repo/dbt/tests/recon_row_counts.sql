-- {{ config(tags=['recon']) }}
-- source manifest count == bronze == silver in + rejected + superseded, per source/date. requirements/05
-- TODO: return rows that VIOLATE the rule (0 rows = pass)
select 1 as _todo where false
