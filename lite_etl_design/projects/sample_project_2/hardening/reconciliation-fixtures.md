# Reconciliation fixtures - Northwind Commerce (DEMO)

> Phase 5 deliverable. Per reconciliation check from `requirements/05` and
> `design/component-design.md` (`reconciliation engine`): the fixtures that force
> a PASS, a FAIL and the tolerance boundary, plus the gate behaviour each must
> produce.

- **Checks source:** `requirements/05-reconciliation.md` (8 checks)
- **Engine:** `recon/gate.py::run_gate` = `dbt test --select tag:recon` +
  `recon/compare.py` manifest compare -> `ReconResult(verdict)`;
  surfaced as the **blocking** Dagster `@asset_check` in
  `northwind_dagster/checks/reconcile.py`
- **Gate on FAIL:** `reconcile` asset check `passed=False` => `publish` /
  `catalog_register` / `advance_watermarks` never materialise, run exits
  non-zero, **no `_SUCCESS`**, `_state.watermarks` unchanged, PagerDuty pages
  Analytics Eng on-call with the `_reconciliation.json` S3 link. **No auto-retry
  of reconciliation** (`05`); the transform may retry once for transient compute.
- **Fixture location:** `build/repo/tests/fixtures/recon/` (seeds in
  `fixtures-catalog.md`: `pass.*`, `fail_count.*`, `fail_total.*`, `boundary.*`,
  `orphan_refund.*` - extend to the full set below)
- **Boundary policy:** unless stated otherwise, a delta **exactly at** tolerance
  is **PASS** (`abs(delta) <= tolerance`). Stated per check.

---

## R1 - Row-count identity  (`05` check 1; tolerance: exact; on fail: block)

Identity per source per `D`: `source_extracted == bronze_landed == silver_in + rejected + superseded`.

| Fixture | Setup | Verdict | Gate action |
|---------|-------|---------|-------------|
| `r1_pass` (`recon/pass.*`) | manifest `row_count` == bronze count == silver-in + rejected + superseded, all 6 sources | **PASS** | publish proceeds |
| `r1_fail_short` (`recon/fail_count.*`) | bronze landed 3 rows short of the manifest for `oltp` | **FAIL** | publish blocked; `_reconciliation.json` names `row_count_identity` / `oltp` / delta `-3` |
| `r1_fail_unaccounted` | silver-in + rejected + superseded is 5 **less** than bronze (rows silently dropped by a join) | **FAIL** | block; report shows the model where the count breaks |
| `r1_boundary` | delta `= 0` exactly (identity holds to the row) | **PASS** | publish (exact check; any non-zero delta fails) |
| `r1_pass_superseded` | POS file re-sent: `bronze` has old + new, `_superseded=true` on the old; silver keeps new only; identity still balances | **PASS** | publish |

## R2 - GMV control total per channel  (`05` check 2; tolerance: ± 0.5%; on fail: block)

`SUM(net_amount in USD)` per channel per `D`: `gold.fct_order` vs the source of
truth - **web** = Shopify payout/summary export, **store** = POS `totals.csv`,
**wholesale** = SFDC closed-won amount.

| Fixture | Setup | Verdict | Gate action |
|---------|-------|---------|-------------|
| `r2_web_pass` | `fct_order` web GMV within ±0.5% of the Shopify payout total | **PASS** | publish |
| `r2_web_fail_high` (`recon/fail_total.*`) | web GMV **1.2%** over the payout total (missing refund offset) | **FAIL** | block; report: channel `web`, expected, actual, delta `+1.2%`, tolerance `0.5%` |
| `r2_store_fail_low` | store GMV **0.9% under** the summed POS `totals.csv` (a store file missing) | **FAIL** | block; report names `store` + the missing `store_id` |
| `r2_wholesale_pass` | SFDC closed-won == `fct_wholesale_opportunity` amount at the **fulfillment** grain | **PASS** (**TODO** Q4: revisit if Finance sets order/invoice grain) | publish |
| `r2_boundary` (`recon/boundary.*`) | delta **exactly +0.5%** | **PASS** (documented: `abs(delta) <= 0.5%`) | publish |
| `r2_boundary_over` | delta `+0.5001%` | **FAIL** | block |
| `r2_control_missing` | POS `totals.csv` absent for `D` | **FAIL** (pre-check), page the **source owner** | block; report: `control_total_missing` / `store` |

## R3 - Refund balancing + linkage  (`05` check 3; exact linkage, amount ± 0.01; on fail: block)

`SUM(refunds) <= SUM(order net)` per customer per period; **every** refund links to an order.

| Fixture | Setup | Verdict | Gate action |
|---------|-------|---------|-------------|
| `r3_pass` | every `fct_refund` row resolves to an `fct_order`; refund totals `<=` order net per customer | **PASS** | publish |
| `r3_orphan` (`recon/orphan_refund.*`) | one refund with no matching `order_id` | **FAIL** | block; report: `refund_linkage`, the `refund_id` |
| `r3_over_refund` | a customer's refunds exceed their order net by 5.00 | **FAIL** | block; report: customer key, delta |
| `r3_boundary` | refunds exactly equal order net (`<=`, so equal is OK); amount diff `= 0.01` | **PASS** | publish (`<=` and `abs <= 0.01`) |
| `r3_late_refund` (`shopify/late_refund.json`) | refund `updated_at` inside the 24h lookback for an older order - order already in a prior `D` | **PASS** (linkage resolves cross-date) | publish; watermark for shopify advances |

## R4 - Order == sum of lines  (`05` check 4; tolerance: ± 0.01; on fail: block)

`gold.fct_order.net_amount` vs `SUM(gold.fct_order_line.net)` per order.

| Fixture | Setup | Verdict | Gate action |
|---------|-------|---------|-------------|
| `r4_pass` | every order's lines sum to the header within 0.01 | **PASS** | publish |
| `r4_fail` | one order's lines sum 0.10 below the header | **FAIL** | block; report: `order_equals_lines`, the `order_id`, delta |
| `r4_boundary` | difference exactly `0.01` | **PASS** (`abs(delta) <= 0.01`) | publish |
| `r4_no_lines` | a header with zero lines | **FAIL** | block (also a DQ `relationships` failure -> the run likely fails earlier) |

Backed by `build/repo/dbt/tests/assert_order_equals_lines.sql` (tag `recon`).

## R5 - FX coverage  (`05` check 5; exact; on fail: block, carry-forward first)

Every `(currency, date)` in `fct_order` / `fct_refund` / `fct_wholesale_opportunity` has a `dim_fx_rate` row.

| Fixture | Setup | Verdict | Gate action |
|---------|-------|---------|-------------|
| `r5_pass` | all currencies present incl. `CAD`; weekday rates | **PASS** | publish |
| `r5_carry_forward` (`fx/weekend.json`) | Saturday `D`, no fresh `open.er-api.com` update; model carries the Friday rate forward | **PASS** after carry-forward | publish; DQ layer emits `warn` (DQ10) |
| `r5_fail_new_ccy` | an order in `AUD`, no `dim_fx_rate` row for `AUD` at any date | **FAIL** | block; report: `fx_coverage`, `AUD`, the `order_date`(s) |
| `r5_fail_gap` | `CAD` present most dates but missing for `D` and no prior rate to carry | **FAIL** | block |
| `r5_boundary` | rate exists dated `D-1`, none for `D`; carry-forward window = 3 days (**TODO** confirm the window with Finance) | **PASS** (within window) | publish + warn |

## R6 - Duplicate check  (`05` check 6; exact; on fail: block)

No unexpected dupes on `order_id`, `(order_id, line_no)`, `refund_id`, `(session_id, session_date)`.

| Fixture | Setup | Verdict | Gate action |
|---------|-------|---------|-------------|
| `r6_pass` | all four keys unique in `gold` for `D` | **PASS** | publish |
| `r6_dupe_order` (`oltp/duplicates.sql`) | `order_id` appears twice in `fct_order` (dedupe missed a case) | **FAIL** | block; report: `duplicate_key`, key `order_id`, the value, count `2` |
| `r6_dupe_session` (`ga4/dupe.parquet`) | `(session_id, session_date)` duplicated | **FAIL** | block |
| `r6_expected_dupe` | same `order_id` across two business dates (legitimate partial fulfilment) | **PASS** - the check is scoped per `D` / per grain; document that cross-date repetition is allowed | publish |

## R7 - Distribution drift vs 28-day baseline  (`05` check 7; ± 30% warn / ± 60% block)

Daily GMV, order count, AOV vs the trailing 28-day baseline table.

| Fixture | Setup | Verdict | Gate action |
|---------|-------|---------|-------------|
| `r7_pass` | GMV / count / AOV within ±30% of baseline | **PASS** | publish |
| `r7_warn` | GMV `+45%` vs baseline (big promo day) | **PASS + WARN** | publish; Slack `#northwind-data` "drift warn: GMV +45%"; on-call eyeballs it |
| `r7_block_high` | order count `+70%` vs baseline (double-load suspected) | **FAIL** | block; report: `distribution_drift`, metric `order_count`, `+70%` |
| `r7_block_low` | GMV `-65%` (a channel silently dropped) | **FAIL** | block |
| `r7_boundary_warn` | exactly `+30%` | **PASS + WARN** (`>= 30%` warns) - documented | publish + warn |
| `r7_boundary_block` | exactly `+60%` | **FAIL** (`>= 60%` blocks) - documented | block |
| `r7_black_friday` | `+400%` on the known Cyber-weekend date | **FAIL** unless the date is on the **expected-spike allowlist** (`TODO` seed `recon_spike_dates.csv`) | block, or PASS+WARN if allowlisted |

## R8 - PII-leak check  (`05` check 8; exact; on fail: block)

No raw email / phone / name in any `gold.*` object (excludes `gold_pii`).

| Fixture | Setup | Verdict | Gate action |
|---------|-------|---------|-------------|
| `r8_pass` | `gold.*` carries only `email_hash`, age band, postcode district | **PASS** | publish |
| `r8_fail_column` | a `gold` model exposes a raw `email` column | **FAIL** | block; report: `pii_leak`, schema.table.column |
| `r8_fail_value` | `email` embedded in a free-text `gold.fct_order.customer_note` value | **FAIL** | block (value-level regex sample) |
| `r8_pass_pii_schema` | real email present, but only in `gold_pii.dim_customer_pii` | **PASS** | publish (scan excludes `gold_pii`) |

Backed by `build/repo/dbt/tests/assert_no_pii_in_gold.sql` (tag `recon`, severity error).

---

## Report assertions (every fixture)

`_reconciliation.json` at `s3://northwind-<env>-lakehouse/_recon/dt=<D>/` contains,
per check: `name`, `applies_to`, `expected`, `actual`, `delta`, `tolerance`,
`verdict`, and on **FAIL** enough to locate the break - `partition` (`D`),
`channel` / `store_id` where relevant, and a `key_sample` (`order_id` /
`refund_id` / `session_id` range). Matches the `CheckResult` dataclass in
`recon/gate.py`. Overall `verdict` is `FAIL` if **any** check is `FAIL`. The
report is also written as an `elementary` row and linked from the PagerDuty page.

## Replay assertion

Run the same business date twice with `r1_pass` + `r2_web_pass` fixtures:

- identical `gold.*` output (row-for-row; `merge` on `unique_key` is idempotent),
- reconciliation **PASS** both times,
- `_state.watermarks` advances **exactly once** (second run is a no-op merge and
  the watermark is already at `D`),
- exactly one `_SUCCESS` object for `dt=<D>`,
- `_reconciliation.json` for the second run overwrites the first with an
  identical body (bytewise, modulo the `run_id` and timestamp fields).

## Weekly whole-dataset hash  (`05` "Granularity")

Not a per-run fixture. A weekly job hashes each `gold.*` table (ordered column
projection) and compares to the prior week's stored hash for unexplained drift;
a mismatch outside the change log opens an issue (not a publish block). Fixture
`r_hash_pass` / `r_hash_drift` under `tests/fixtures/recon/weekly/`.
