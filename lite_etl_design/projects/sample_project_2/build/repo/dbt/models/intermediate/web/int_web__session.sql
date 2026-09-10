-- int_web__session
-- Implements: transformation-design.md s.2; requirements/03 business rules
{{ config(materialized='ephemeral') }}

-- TODO: joins / dedupe / currency->USD / identity hash per requirements/03
select 1 as _todo
