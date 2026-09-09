# Source intake (EXAMPLE - filled in)

- Source name (slug): finance_customers
- Domain: finance
- Owning team / contact: Data Platform / dp-oncall
- System of record: PostgreSQL (billing DB, read replica)
- Connection type: rdbms
- How we reach it: host=replica.billing.internal db=billing table=public.customers
- Auth method: vault path `secret/data/etl/billing_ro`
- Object(s) to extract: SELECT * FROM public.customers WHERE updated_at > :watermark
- Extract mode: incremental
- Watermark column: updated_at
- Expected volume: ~50k rows/day, < 200 MB/day
- Frequency / SLA: hourly, landed + reconciled within 20 min of the hour
- Format & encoding: n/a (DB); land as parquet, UTF-8; timestamps to UTC
- Known quirks: name has trailing spaces; country lowercase; some NULL emails
- Downstream use: dwh.dim_customer
