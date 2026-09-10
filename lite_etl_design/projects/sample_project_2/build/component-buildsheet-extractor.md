# Component buildsheet: `extractor` (framework + 6 source modules)

- **Design refs:** `design/component-design.md#extractor`,
  `design/data-flow-diagram.md` (4 source shapes), `requirements/01` (per-source
  detail + quirks), `requirements/02` (run identity, POS supersede)
- **Language / framework:** Python 3.12; `httpx` (APIs), `psycopg`/SQLAlchemy
  (Postgres), `boto3` (S3), `google-cloud-bigquery` (GA4), `pyarrow` (Parquet)
- **Repo path:** `build/repo/extractors/`

## Files to create

| Path | Purpose |
|------|---------|
| `build/repo/extractors/common/base.py` | `Extractor` ABC: `plan()`, `run()`, shared retry/paging/manifest helpers |
| `build/repo/extractors/common/http.py` | retrying HTTP client (429/5xx expo backoff, `Retry-After`), for shape B/D |
| `build/repo/extractors/oltp.py` | Postgres incremental (`updated_at`, 60-min lookback), 4 tables |
| `build/repo/extractors/shopify.py` | Shopify Admin REST, cursor pagination, `updated_at_min`, drop `test=true` |
| `build/repo/extractors/pos.py` | S3 CSV.gz per store; gunzip + parse (cents/100, tz->UTC); `_file_etag` |
| `build/repo/extractors/salesforce.py` | Bulk API 2.0 jobs, `SystemModstamp`, `queryAll` for deletes |
| `build/repo/extractors/ga4.py` | BigQuery job: aggregate prior-day events -> session grain -> Parquet to inbound |
| `build/repo/extractors/fx.py` | single GET open.er-api.com; carry-forward flag on gap |
| `build/repo/extractors/config/{oltp,shopify,pos,salesforce,ga4,fx}.yml` | per-source config (objects, lookback, page size) - **no secrets** |
| `build/repo/tests/unit/test_{oltp,shopify,pos,salesforce,ga4,fx}.py` | one per source |

## Public interface (every source module)

- **`class <Src>Extractor(Extractor)`** with:
  - **`plan(business_date: date, run_id: str) -> ExtractPlan`** - resolve
    watermark, compute the window / file list / API params.
  - **`run(plan: ExtractPlan) -> ExtractResult`** - fetch, write Parquet to a
    staging path, return row counts + checksums + `_source_file` list + the new
    high-watermark (staged, not committed). Does **not** write to `bronze`
    directly - hands the Parquet + metadata to `landing`.
- **Inputs:** `Settings` (from `config`), secret refs (via `secrets.resolve`),
  staged watermark (via `StateStore`).
- **Outputs:** local/staged Parquet files; an `ExtractResult` dataclass
  (`rows`, `files`, `checksums`, `new_watermark`, `warnings`).
- **Config keys** (per `extractors/config/<src>.yml`): `objects` (table/endpoint
  list), `lookback_minutes`, `page_size`, `timeout_s`, source-specific
  (`shopify.api_version`, `pos.key_template`, `ga4.dataset`, `fx.base_ccy`).

## Key logic (per shape - from `data-flow-diagram.md`)

- **A (oltp / shopify / salesforce):** `watermark - lookback` filter -> page ->
  Parquet -> `new_watermark = max(updated_at seen)`. Shopify: follow `Link`
  header, honour `Retry-After`, drop `test=true`. SFDC: Bulk job poll loop.
- **B (pos):** list S3 keys under `pos/dt=<D>/`; for each `store` take the
  latest `file_etag`; gunzip; parse CSV (`\N` nulls, `amount_cents/100`,
  `txn_ts` + `store_tz` -> UTC); emit `_file_etag` per row so `landing` can
  supersede.
- **C (ga4):** submit a BigQuery SQL job that aggregates `events_<D-2>` to
  session grain; export result to Parquet in inbound; `_ingest_date = D-2`.
- **D (fx):** one GET; if a currency/date is missing, carry forward the last
  known rate and set `is_carried_forward = true`.

## Unit tests to write (per source)

| Test | Fixture | Asserts |
|------|---------|---------|
| happy path | `fixtures/<src>/sample.*` | row count, columns, `new_watermark`, checksum stable |
| empty window | `fixtures/<src>/empty.*` | 0 rows, no error, watermark unchanged |
| idempotent re-run | run `plan`+`run` twice on same input | identical `ExtractResult` (bar `run_id`) |
| retry then succeed | mock 429 then 200 (`http` client) | one retry, then success; backoff respected |
| retry exhausted | mock 429 x4 | raises `ExtractFailed`, nothing written |
| late data | `fixtures/<src>/late_data.*` | rows before watermark still captured within lookback |
| duplicates | `fixtures/<src>/duplicates.*` | passed through (dedupe is dbt's job) with a warning |
| schema drift | `fixtures/<src>/schema_drift.*` | detected, `warnings` set, `run` still writes (drift check is post-land) |
| bad rows / encoding | `fixtures/<src>/bad_rows.*` | rows written verbatim (DQ routing is dbt's job) |
| POS supersede (`pos` only) | two etags for `(D, store)` | only latest-etag rows in the result, `_file_etag` column present |
| POS partial file (`pos` only) | `fixtures/pos/partial.csv` | trailing blank line ignored, count correct |
| test-order filter (`shopify` only) | `fixtures/shopify/sample.json` w/ `test=true` | those rows dropped |
| carry-forward (`fx` only) | `fixtures/fx/weekend.json` | missing ccy carried, `is_carried_forward=true` |

## Fixtures needed

Per source: `sample`, `empty`, `late_data`, `duplicates`, `schema_drift`,
`bad_rows`; `pos` also `partial.csv` + two-etag pair; `fx` also `weekend.json`.
All tiny, synthetic, **no PII** (fake emails like `a@example.test`). See
`fixtures-catalog.md`.

## Done checklist

- [ ] 6 modules + `common/base.py` + `common/http.py` created
- [ ] every source: happy + all failure modes + idempotent re-run tested
- [ ] no hostnames / tokens in code - `extractors/config/<src>.yml` +
      `secret-scope://` refs only
- [ ] `GA4` aggregation SQL marked `TODO` pending the event schema (O3)
- [ ] wired into `make test`
