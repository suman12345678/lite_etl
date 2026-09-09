# 02 - Targets & loading

## Target platform

- **Platform:** BigQuery / Snowflake / Redshift / Synapse / Delta / Iceberg /
  relational DB / files
- **Target database / dataset / schema:**
- **Naming conventions:** (tables, columns, staging vs curated)
- **Region / project / account:**

## Landing / staging zone

- **Required?** yes / no
- **Location:** path / bucket / schema
- **Format:** Parquet (default) / CSV / JSON / Avro
- **Layout:** e.g. `<domain>/<source>/<load_date>/<run_id>/`
- **Retention:** keep / archive / purge after N days

## Load patterns

| Target table | Pattern | Business key | Surrogate key? | Partition / cluster | Notes |
|--------------|---------|--------------|----------------|---------------------|-------|
| | append / upsert / SCD2 / truncate-reload / snapshot | | | | |

## Idempotency & replay

- **Run identity:** how a run is uniquely identified
- **Re-run safety:** how a repeated run avoids double-loading
- **Rollback:** how a bad load is undone / superseded
- **Watermark advance:** only after reconciliation passes? yes / no

## Backfill at go-live

- **Needed?** how far back, expected volume, one-off or windowed
