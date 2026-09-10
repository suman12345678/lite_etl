-- Singular test: no raw email/phone/name string columns present in any gold.* object. requirements/08
-- TODO: return rows that VIOLATE the rule (0 rows = pass)
select 1 as _todo where false
