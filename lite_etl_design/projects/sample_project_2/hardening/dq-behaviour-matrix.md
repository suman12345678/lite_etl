# DQ behaviour matrix - Northwind Commerce (DEMO)

> Phase 5 deliverable. Every data-quality rule from `requirements/04-data-quality.md`
> crossed with the input scenarios that exercise it, and the routing the pipeline
> must produce. Executable spec for the dbt tests / DQ engine.

- **Rules source:** `requirements/04-data-quality.md`
- **Implemented as:** dbt generic + `dbt_expectations` + singular tests + `elementary`
  anomaly detection (`design/transformation-design.md` s.6; `10` s."Transformation framework")
- **Routing outcomes:** `pass` | `warn` (load + Slack `#northwind-data`) |
  `quarantine` (row -> `reject__<entity>` with `reason_code`, `_run_id`, `_dq_rule`) |
  `fail` (abort `curated_build`, no publish, page Analytics Eng on-call)
- **Evaluation grain:** per business date `D` (per `04` "Thresholds")
- **Reject tables:** `silver` reject tables (`component-design.md` dbt-runner outputs)

## Global thresholds (`04` "Thresholds")

| Scenario | Quarantine rate for an entity | Expected |
|----------|------------------------------|----------|
| below warn | `< 0.1%` | run proceeds silently (`pass`) |
| warn band | `0.1% .. 0.5%` | run proceeds, `warn` alert to Slack |
| **at fail threshold** | `= 0.5%` | **fail** (`> 0` quarantined AND rate `>= 0.5%`; boundary is inclusive - documented here) |
| above fail | `> 0.5%` | **fail** run, nothing publishes, reject table retained |
| any `error`-severity generic test fails | n/a | **fail** run regardless of rate |

## Matrix

### DQ01 - `stg_oltp__orders.order_id` not null + unique  (`04` concrete rule 1; dimension: completeness + uniqueness)

| Scenario (fixture) | Expected routing | Threshold effect | Test |
|--------------------|------------------|------------------|------|
| all `order_id` present + unique (`oltp/sample.sql`) | pass | - | `not_null`, `unique` (generic, severity error) |
| one null `order_id` (`oltp/bad_rows.sql`) | **fail** run | any error generic test fail => fail | `not_null` |
| duplicate `order_id` two rows (`oltp/duplicates.sql` adapted) | **fail** run (staging is pre-dedupe; dupes here are real) | error | `unique` |
| dup that `qualify_dedupe` resolves upstream (same `customer_id`, later `updated_at`) | pass (latest kept) | - | `qualify_dedupe` macro + `unique` after |

### DQ02 - `fct_order.currency` in `currency_list` seed  (rule 2; validity)

| Scenario | Routing | Test |
|----------|---------|------|
| `GBP` / `USD` / `CAD` all in seed (`shopify/sample.json` CAD order) | pass | `accepted_values` from `ref('currency_list')` |
| `XYZ` not in seed | **fail** run | `accepted_values` (severity error) |
| currency missing / null | **fail** run | `not_null` + `accepted_values` |

### DQ03 - `fct_order.gmv >= 0` unless `is_return`  (rule 3; validity)

| Scenario | Routing | Threshold effect | Test |
|----------|---------|------------------|------|
| positive gmv, non-return | pass | - | `dbt_expectations.expect_column_values_to_be_between(min=0)` where `not is_return` |
| negative gmv, `is_return = true` | pass | - | predicate excludes returns |
| negative gmv, `is_return = false` (`oltp/bad_rows.sql` negative price) | **quarantine** row, `reason_code = neg_gmv_non_return` | counts toward the 0.5% entity threshold | singular + reject insert |
| negative gmv on `>= 0.5%` of `D`'s `fct_order` rows | **fail** run | rate breach | threshold test on reject count |

### DQ04 - `fct_order.order_date` in `[2015-01-01, current_date]`  (rule 4; timeliness / validity)

| Scenario | Routing | Test |
|----------|---------|------|
| date within range | pass | `dbt_expectations.expect_column_values_to_be_between` |
| `order_date` in the future | **fail** run ("no future `order_date`", `04` dimensions) | severity error |
| `order_date` before 2015-01-01 (historical backfill edge) | **fail** run - **TODO** confirm with Commerce whether pre-2015 backfill is in scope (Q: `00` says 24 months, so not expected) | severity error |

### DQ05 - `fct_order_line` sum(net) per order == `fct_order.net_amount` (± 0.01)  (rule 5; consistency)

| Scenario | Routing | Test |
|----------|---------|------|
| lines sum to header within 0.01 | pass | singular `assert_order_equals_lines.sql` (exists in `build/repo/dbt/tests/`) |
| lines sum off by 0.05 | **fail** run | singular, severity error |
| header has no lines (orphan header) | **fail** run | singular (also a `relationships` view) |
| rounding: sum differs by exactly 0.01 | pass (tolerance inclusive - documented) | singular uses `abs(diff) <= 0.01` |

### DQ06 - `net = gross - discount + tax` per line  (`04` dimensions "consistency")

| Scenario | Routing | Test |
|----------|---------|------|
| identity holds within 0.01 | pass | singular / `dbt_expectations` row-level |
| identity violated | **quarantine** row, `reason_code = net_identity` | counts to threshold | singular + reject |
| tax or discount null (treated as 0) | pass if identity still holds; else quarantine | coalesce in the model, test post-coalesce |

### DQ07 - `dim_customer.email_hash` matches `^[a-f0-9]{64}$`  (rule 6; validity + security)

| Scenario | Routing | Test |
|----------|---------|------|
| 64-char lowercase hex | pass | `dbt_expectations.expect_column_values_to_match_regex` |
| raw email leaked into `email_hash` | **fail** run | regex fails (contains `@`) - also caught by DQ08 |
| uppercase hex / wrong length | **fail** run | regex, severity error |
| null `email_hash` for a customer with no email on file | pass **only if** business allows anon customers - **TODO** confirm; default = `warn` + load with sentinel | conditional `not_null` (severity warn) |

### DQ08 - PII-leak: no raw email / phone / name in any `gold.*`  (rule 7; `08`; ADR-006)

| Scenario | Routing | Test |
|----------|---------|------|
| `gold.*` has only `email_hash`, age band, postcode district | pass | singular `assert_no_pii_in_gold.sql` (exists), severity error |
| raw `email` column present in a `gold` model | **fail** run, **block publish** | singular scans `information_schema` + regex-samples values |
| free-text `notes` column containing an email address | **fail** run | singular value-level regex sample (not just column names) - **TODO** confirm the sampling approach covers `gold.fct_order.customer_note` if that column exists |
| PII only in `gold_pii.*` | pass | scan excludes the `gold_pii` schema by design |

### DQ09 - `stg_shopify__orders` `test = true` rows == 0 after filter  (rule 8; validity)

| Scenario | Routing | Test |
|----------|---------|------|
| all `test = true` filtered in staging (`shopify/sample.json` has one) | pass | singular: `count(*) where test` == 0 on the staging model, severity **warn** |
| a `test = true` order reaches `stg` | **warn**, alert to Slack, row still loaded then excluded downstream | severity warn (`04` says warn) |

### DQ10 - `dim_fx_rate` covers every currency/date in `fct_order`  (rule 9; referential / accuracy) - also recon check FX coverage

| Scenario | Routing | Test |
|----------|---------|------|
| every `(currency, order_date)` has a rate | pass | singular / `relationships` to `dim_fx_rate` |
| weekend / holiday - no fresh rate (`fx/weekend.json`) | **carry-forward** last good rate, then **warn** | model applies carry-forward; test asserts coverage after carry-forward, severity warn |
| currency with no rate at all (new market) | **fail** run in **reconcile** (FX coverage is a blocking recon check, `05`); DQ layer = warn | see `reconciliation-fixtures.md` FX section |

### DQ11 - `fct_web_session.events > 0`  (rule 10; completeness)

| Scenario | Routing | Test |
|----------|---------|------|
| session with `>= 1` event | pass | model filters `events > 0` |
| session with `events = 0` (`ga4/zero_event.parquet`) | **drop row** + **warn** (count of drops in the DQ report) | severity warn; drop is in the model, test asserts the drop happened |

### DQ12 - every `bronze.*` row has `_run_id` not null  (rule 11; completeness / lineage)

| Scenario | Routing | Test |
|----------|---------|------|
| landing writer tags every row | pass | `not_null(_run_id)` on every `source` / staging model |
| a row without `_run_id` (landing bug) | **fail** run | severity error - blocks the whole `D` because lineage is unprovable |

### DQ13 - referential integrity: every fact `_sk` resolves, else `-1` + warn  (`04` dimensions)

| Scenario | Routing | Test |
|----------|---------|------|
| `customer_sk` / `product_sk` / `store_sk` / `account_sk` all resolve | pass | `relationships` generic on each fact FK |
| parent missing -> row keyed to unknown-member `-1` | **warn** (load with `-1`), count in DQ report | model does the `-1` mapping; `relationships` on the *raw* key = severity warn |
| `-1` share `> 0.5%` of a fact for `D` | **fail** run | threshold test on the `-1` count |

### DQ14 - `dbt source freshness`  (`04` "Timeliness"; `10` s."Sources & freshness")

| Scenario | Routing | Test |
|----------|---------|------|
| source loaded within `warn_after` (6h, tuned per source vs cadence) | pass | `dbt source freshness` |
| source stale between `warn_after` and `error_after` (6-12h) | **warn**, Slack, `curated_build` still runs | freshness warn band |
| source stale past `error_after` (12h) | **fail** the run at the `source_freshness` gate asset; do **not** run `curated_build`; page | freshness error band |
| **NOTE** | `source_freshness` is currently a `TODO` in `northwind_dagster/assets/transform.py`, not a scaffolded asset (Phase 4 `/validate-config` #15). Implementing it as a gate `@asset` upstream of `curated_build` is a go-live blocker. | - |

### DQ15 - schema-drift check vs `sources.yml`  (pipeline-blueprint.md; policy = fail)

| Scenario (fixture) | Routing | Test |
|--------------------|---------|------|
| source schema matches the contract | pass | contract check post-land (per source `schema_drift.*` fixtures exist) |
| added column (`oltp/schema_drift.sql` extra `promo_code`) | **halt** the run + open a ticket + **page** on-call + source owner (policy = fail, `04`/`component-design.md`) | drift check, `curated_build` does not start |
| removed / retyped column (`shopify/schema_drift.json` missing `presentment_currency`; `pos/schema_drift.csv.gz` reordered header; `salesforce/schema_drift.csv` missing `SystemModstamp`) | **halt** + ticket + page | same |
| **NOTE** | `schema_drift` is also a `TODO` comment, not a scaffolded asset (`/validate-config` #15). | - |

## Reporting assertions

- Each quarantined row lands in `reject__<entity>` with `reason_code`, `_run_id`,
  `_dq_rule`, `_dq_ts`, and the offending value(s).
- The **Elementary** dashboard shows, per model per run: generic-test pass count,
  singular-test results, quarantine count and rate, and the 7-day pass-rate trend
  (target `>= 99.5%`, `04`).
- A **daily DQ digest** posts to `#northwind-data` (Slack) listing warn-band
  entities and any Elementary anomaly.
- On a **fail**: PagerDuty page to Analytics Eng on-call with the failing
  test/entity, the reject-rate, and a link to the run.
- `dq_score` per model (Elementary pass-rate) is written to the metrics backend
  for the DQ dashboard (`observability-wiring.md`).

## Traceability

| Matrix rows | Requirement |
|-------------|-------------|
| DQ01-DQ13 | `requirements/04` "Concrete rules" + "Dimensions to enforce" |
| Thresholds block | `04` "Thresholds" (0.5% fail / 0.1% warn, per business date) |
| DQ14 | `04` "Timeliness" + `10` freshness `warn_after 6h / error_after 12h` |
| DQ15 | `design/pipeline-blueprint.md` schema-drift check; `component-design.md` extractor failure modes (policy = fail) |
| DQ08 | `requirements/08` PII treatment table; ADR-006; `dbt/tests/assert_no_pii_in_gold.sql` |
| Reporting | `04` "Reporting & ownership"; `design/component-design.md` observability |
