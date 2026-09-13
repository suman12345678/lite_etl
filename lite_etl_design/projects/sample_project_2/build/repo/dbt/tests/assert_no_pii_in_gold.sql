{{ config(tags=['recon', 'slice'], severity='error') }}
-- R8 / DQ08 (requirements/08, ADR-006): no raw email / phone / name column in any
-- gold-facing model. Scans information_schema for column names that look like raw
-- PII (an *_hash column is fine). Returns offenders (0 rows = PASS). The full build
-- adds gold_pii exclusion + value-level sampling of free-text columns.

select table_schema, table_name, column_name
from information_schema.columns
where table_schema in ('gold', 'main')          -- gold-facing; 'main' is the ci default
  and lower(column_name) not like '%hash%'
  and (
        lower(column_name) in ('email', 'phone', 'phone_number', 'first_name',
                               'last_name', 'full_name', 'name', 'address', 'dob', 'date_of_birth')
     or lower(column_name) like '%email%'
     or lower(column_name) like '%phone%'
  )
