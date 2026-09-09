# Source intake

> Fill one per data source. Drop the completed file in `requirements/inbox/`.

- **Source name (slug):**            e.g. `finance_customers`
- **Domain / subject area:**         e.g. `finance`
- **Owning team / contact:**
- **System of record:**              e.g. Oracle ERP, Salesforce, an SFTP drop
- **Connection type:**               csv | rdbms | rest_api | s3 | gcs | azure_blob | sftp | bigquery | snowflake | kafka | other
- **How we reach it:**               host / URL / bucket / path / table / query (no passwords here)
- **Auth method:**                   env var / vault path / key file / IAM role / OAuth
- **Object(s) to extract:**          table name(s), query, file glob, API endpoint(s)
- **Extract mode:**                  full | incremental | cdc | file-arrival
- **Watermark column (if incremental):**  e.g. `updated_at`
- **Expected volume:**               rows/day, GB/day, file count
- **Frequency / SLA:**               e.g. hourly, daily by 06:00 UTC
- **Format & encoding:**             delimiter, header, encoding, date/number formats
- **Known quirks:**                  nulls-as-text, trailing spaces, timezone, partial files
- **Downstream use:**                which warehouse tables / consumers
