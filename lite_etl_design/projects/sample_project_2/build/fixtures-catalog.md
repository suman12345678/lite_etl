# Fixtures catalog - Northwind Commerce (DEMO)

> Phase 3 deliverable. Every fixture the unit tests + `dbt --target ci` need, by
> source. Fixtures are tiny, committed, and contain **no real data or secrets**
> (fake emails are `<name>@example.test`). Edge cases come from the "Known
> quirks" in `requirements/01` and the DQ rules in `requirements/04`.

- **Location:** `build/repo/tests/fixtures/`
- **Golden outputs:** `build/repo/tests/golden/`

## Per source

### `oltp` (Postgres: customers, products, orders, order_lines)

| Fixture file | Represents | Used by |
|--------------|-----------|---------|
| `oltp/sample.sql` | ~15 rows across the 4 tables, one full order | extractor happy path, `dbt --target ci` |
| `oltp/empty.sql` | schema only, 0 rows | empty-window test |
| `oltp/late_data.sql` | rows with `updated_at` 30 min before the watermark | lookback test |
| `oltp/duplicates.sql` | same `customer_id` twice with different `updated_at` | dedupe (dbt) test |
| `oltp/schema_drift.sql` | `orders` with an extra `promo_code` column | drift-check test |
| `oltp/bad_rows.sql` | null `order_id`, negative price, bad UTF-8 in `name` | DQ routing test |
| `oltp/soft_delete.sql` | rows with `is_deleted = true` | staging must exclude them |

### `shopify` (Admin REST: orders, refunds, fulfillments)

| Fixture file | Represents | Used by |
|--------------|-----------|---------|
| `shopify/sample.json` | 5 orders (incl. one `test=true`, one CAD, one partial refund), paginated over 2 pages | happy path, currency + test-filter tests |
| `shopify/empty.json` | `{"orders": []}` | empty test |
| `shopify/rate_limited.json` + a 429 script | first call 429 w/ `Retry-After: 1`, then 200 | retry test |
| `shopify/late_refund.json` | a refund `updated_at` inside the 24h lookback for an older order | late-data test |
| `shopify/schema_drift.json` | order missing `presentment_currency` | drift test |

### `pos` (S3 CSV.gz per store + totals.csv)

| Fixture file | Represents | Used by |
|--------------|-----------|---------|
| `pos/dt=2026-09-08/store=001/txns.csv.gz` | ~20 rows, cents amounts, `store_tz=Europe/London` | happy path |
| `pos/dt=2026-09-08/store=001/txns_v2.csv.gz` (new etag) | same day corrected | supersede test |
| `pos/dt=2026-09-08/store=001/totals.csv` | store daily totals | reconciliation control total |
| `pos/partial.csv.gz` | truncated file + trailing blank line | partial-file test |
| `pos/bad_rows.csv.gz` | `\N` in required field, non-numeric amount | DQ routing |
| `pos/schema_drift.csv.gz` | reordered / renamed header | drift test |

### `salesforce` (Bulk API: Account, Contact, Opportunity, OpportunityLineItem)

| Fixture file | Represents | Used by |
|--------------|-----------|---------|
| `salesforce/sample/*.csv` | one account, two contacts, one closed-won opp + 2 lines | happy path |
| `salesforce/deleted.csv` | `IsDeleted = true` rows (from `queryAll`) | delete-handling test |
| `salesforce/empty/*.csv` | headers only | empty test |
| `salesforce/schema_drift.csv` | missing `SystemModstamp` | drift test |

### `ga4` (BigQuery extract -> Parquet session grain)

| Fixture file | Represents | Used by |
|--------------|-----------|---------|
| `ga4/sample.parquet` | ~10 sessions, one with a `login` event carrying a hashed email | happy path, identity-join test |
| `ga4/zero_event.parquet` | a session with `events = 0` | drop-row test |
| `ga4/dupe.parquet` | duplicate `(session_id, session_date)` | dedupe test |
| `ga4/late_shard.parquet` | fewer rows than expected for the shard | "shard not final" skip test |

### `fx` (open.er-api.com)

| Fixture file | Represents | Used by |
|--------------|-----------|---------|
| `fx/sample.json` | full `rates` map for a weekday | happy path |
| `fx/weekend.json` | missing update / stale `time_last_update` | carry-forward test |
| `fx/error_503.json` + script | 503 then 200 | retry test |

## Reconciliation fixtures (shared with Phase 5)

| Fixture | Scenario | Expected gate |
|---------|----------|---------------|
| `recon/pass.*` | manifest == bronze == silver; GMV within ±0.5% | PASS |
| `recon/fail_count.*` | bronze short by 3 rows vs manifest | FAIL, no publish |
| `recon/fail_total.*` | `web` GMV 1.2% over the payout control total | FAIL |
| `recon/boundary.*` | GMV delta exactly ±0.5% | documented (PASS) |
| `recon/orphan_refund.*` | a refund with no matching order | FAIL |

## Golden outputs

| Golden file | For | Notes |
|-------------|-----|-------|
| `golden/dim_customer.csv` | `dbt --target ci` on the `sample` fixtures | regenerate with `make golden` on an intentional logic change |
| `golden/fct_order.csv` | as above | |

## Rules

- No PII, no production rows. Fake everything. Emails `@example.test`.
- Each fixture < a few KB; one concern per fixture.
- A new failure mode in a buildsheet must add a fixture here.
