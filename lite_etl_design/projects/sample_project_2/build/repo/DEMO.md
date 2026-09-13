# Runnable demo — `northwind_daily` walking skeleton

A **real, runnable** slice of the pipeline on DuckDB — no cloud, no Databricks, no
Dagster. Two ways to run it: `make demo` (pure Python + DuckDB, zero extra deps)
and `make dbt-ci` (the same slice as real dbt models). It exists so you can *show*
the three things this project is about:

1. **data load** — synthetic fixtures land as `bronze.*`
2. **data quality + correction** — the rule `gmv >= 0 unless is_return`
   quarantines a bad row into `reject__fct_order`; fixing it at source and
   re-running clears it
3. **the reconciliation gate** — row-count identity, GMV vs a control total, and
   `order == sum(lines)`; **PASS** publishes to `gold` and writes `_SUCCESS`,
   **FAIL** blocks the publish and exits non-zero

The slice is `oltp` + `fx` → `stg_*` → `int_orders_usd` → `dim_customer` /
`dim_fx_rate` / `fct_order` / `fct_order_line` (+ `reject__fct_order`). The other
4 sources and the full 8 reconciliation checks follow the same shape.

## Run it

```bash
cd build/repo
uv venv && uv pip install -e ".[dev]"     # or: pip install duckdb pyyaml

make demo          # bad source data -> 1 row quarantined -> reconciliation PASS -> publish
make demo-good     # clean data, nothing quarantined
make demo-fixed    # the quarantined row corrected at source -> re-run green (control total updated)
make demo-fail     # force a reconciliation FAIL -> publish blocked, exit 1
```

(direct: `python -m demo.run --dataset {good|bad|fixed} [--control-totals {pass|fail}] [--date 2026-09-08]`)

## What each run prints

```
1. LOAD       bronze.oltp__customers / __orders / __order_lines / __products, bronze.fx__rate  + row counts
2. TRANSFORM  bronze -> stg -> int -> dim/fct ; DQ rule DQ03 quarantine list (order id, reason_code, rule)
3. RECONCILE  the 3 checks with expected / actual / delta / tolerance / verdict
              -> .local_state/_recon/dt=<D>/_reconciliation.json   (same shape as recon/gate.py)
4. GATE       PASS -> gold.fct_order + .local_state/gold/_SUCCESS_dt=<D> ; FAIL -> "PUBLISH BLOCKED", exit 1
```

## How the scenarios work — same pipeline, different inputs

**Every run executes the whole slice, unchanged.** `demo/run.py` always does the
same five things in the same order:

```
load fixtures -> bronze.*          (demo/load.py)
run staging SQL                    (demo/sql/10_staging.sql)
run marts SQL + the DQ rule        (demo/sql/20_marts.sql  -> fct_order, reject__fct_order)
run the 3 reconciliation checks    (demo/checks.py)
PASS -> publish gold + _SUCCESS  |  FAIL -> block + exit 1   (demo/run.py)
```

The command-line flags **do not change the code path** - they only pick which
input files that one pipeline reads:

| Flag | Swaps in… | Effect |
|------|-----------|--------|
| `--dataset good` | `tests/fixtures/oltp/sample.sql` as the raw orders | 4 clean orders |
| `--dataset bad` | `tests/fixtures/oltp/bad_rows.sql` | same 4 + order 1005 (`-42.00`, not a return) |
| `--dataset fixed` | `tests/fixtures/oltp/bad_rows_fixed.sql` | order 1005 corrected to `+42.00` |
| `--control-totals pass` | `tests/fixtures/recon/control_totals_pass.csv` (`direct,200.00`) | the GMV check compares against 200.00 |
| `--control-totals fail` | `tests/fixtures/recon/control_totals_fail.csv` (`direct,260.00`) | compares against 260.00 → mismatch |
| `--control-totals fixed` | `tests/fixtures/recon/control_totals_fixed.csv` (`direct,242.00`) | matches the corrected data |

If you omit `--control-totals`, it defaults from `--dataset` (`good`/`bad` →
`pass`, `fixed` → `fixed`). So the four demo scenarios are just four
(orders file, control-total file) pairs run through the identical pipeline.

## Where the rules live

Two layers - the **spec** (what the rule is) and the **implementation** (the code
that enforces it):

| Rule | Spec (the requirement) | Phase 5 expansion | Runs in the demo as |
|------|------------------------|-------------------|---------------------|
| **DQ03** `gmv >= 0 unless is_return` → quarantine | `requirements/04-data-quality.md`, "Concrete rules" table, row `fct_order.gmv` | `hardening/dq-behaviour-matrix.md` row **DQ03** | a `WHERE` clause in `demo/sql/20_marts.sql` that fills `reject__fct_order` |
| **R1** row-count identity | `requirements/05-reconciliation.md`, check 1 | `hardening/reconciliation-fixtures.md` **R1** | `demo/checks.py::row_count_identity` |
| **R2** GMV vs control total, ±0.5% | `requirements/05-reconciliation.md`, check 2 | `hardening/reconciliation-fixtures.md` **R2** | `demo/checks.py::gmv_control_total` |
| **R4** order == sum(lines), ±0.01 | `requirements/05-reconciliation.md`, check 4 | `hardening/reconciliation-fixtures.md` **R4** | `demo/checks.py::order_equals_lines` |
| the **thresholds** (`0.5%` tolerance, `0.5%` fail rate) | `requirements/04` "Thresholds" + `05` tolerances | - | `config/defaults.yml` (`recon.tolerance_pct`, `dq.fail_threshold_pct`); `run.py` reads it on start-up |

The requirement files **describe** the rules in prose/tables; they don't execute.
The demo (and, in the real build, the dbt tests + `recon/gate.py`) is where they
become code. The demo covers 1 DQ rule and 3 of the 8 reconciliation checks;
`requirements/04` has ~15 rules and `requirements/05` has 8 checks - the rest
follow the same pattern.

## Presenter guide

### 30-second framing (say this first)

> "This is a tiny fake retail pipeline. It takes made-up sales orders, **catches a
> bad order**, **checks the money adds up against finance's total**, and then
> either **publishes** the clean data or **blocks** it. Runs on my laptop in two
> seconds — the real one runs on Databricks + dbt + Dagster, same shape."

### Setup (once, before the room is watching)

```bash
cd build/repo
python -m venv .venv && .venv\Scripts\activate      # macOS/Linux: source .venv/bin/activate
pip install duckdb pyyaml
python -m demo.run --dataset good                    # smoke-test it prints 4 sections and "GATE VERDICT: PASS"
```

`make` is optional — every `make <x>` below is a shortcut for the `python -m demo.run` line under it.

### The run sheet (≈5 minutes)

| # | Command | What to say while it runs |
|---|---------|---------------------------|
| 1 | `make demo-good`  → `python -m demo.run --dataset good` | "Clean data. Section 1 loads 4 orders as `bronze.*`. Section 2 transforms them and converts every currency to USD. Section 3 runs 3 reconciliation checks — all green. Section 4: **published** to `gold` with a `_SUCCESS` marker." |
| 2 | `make demo`  → `python -m demo.run --dataset bad` | "Now there are 5 orders and one is bad — order 1005, **−42.00 USD and it's not a refund**. Look at Section 2: the data-quality rule **quarantines it** into `reject__fct_order` with a reason code. It never reaches `gold`. The other 4 still reconcile, so we still publish. Bad row caught, good data flows." |
| 3 | `make demo-fail`  → `python -m demo.run --dataset bad --control-totals fail` | "Same data — but finance's control total for the day says **260.00** and we only have **200.00**. Section 3: `gmv_control_total` **FAILs** (23% gap, tolerance is 0.5%). Section 4: **PUBLISH BLOCKED** — nothing written to `gold`, no `_SUCCESS`, and it **exits non-zero** so CI fails and on-call gets paged. Numbers that don't reconcile cannot get published." |
| 4 | `make demo-fixed`  → `python -m demo.run --dataset fixed` | "Someone fixed order 1005 at source (−42 → +42) and finance re-issued the control total to match (242.00). Re-run: **nothing quarantined, totals match, published.** That's the correction loop." |
| 5 | *(optional, live edit — see below)* | "Let me break it in front of you." |

### The live-edit finale (optional, high impact)

Open a fixture, change one number, re-run — the gate reacts. Change it back afterwards.

| Edit | File | Re-run | Result |
|------|------|--------|--------|
| control total `200.00` → `205.00` | `tests/fixtures/recon/control_totals_pass.csv` | `python -m demo.run --dataset good` | `gmv_control_total` FAILs (2.5% gap) → PUBLISH BLOCKED |
| order `1002` amount `120.00` → `-9.00` (leave `is_return` = `false`) | `tests/fixtures/oltp/sample.sql` | `python -m demo.run --dataset good` | order 1002 shows in the Section 2 reject list; GMV then drops to 80.00 so `gmv_control_total` also FAILs → PUBLISH BLOCKED |
| an `order_lines` row amount so it no longer sums to its order | `tests/fixtures/oltp/sample.sql` | `python -m demo.run --dataset good` | `order_equals_lines` FAILs → PUBLISH BLOCKED |

Reset with `git checkout tests/fixtures/` (or undo in the editor).

### The made-up data, in one screen

`tests/fixtures/oltp/sample.sql` — the clean orders (`net_amount` is in the order's own currency):

| order | customer | currency | net_amount | is_return | → USD |
|-------|----------|----------|-----------:|-----------|------:|
| 1001 | 1 (GB) | GBP | 39.00 | false | 50.00 |
| 1002 | 2 (US) | USD | 120.00 | false | 120.00 |
| 1003 | 3 (CA) | CAD | 68.00 | false | 50.00 |
| 1004 | 1 (GB) | GBP | −15.60 | **true** | −20.00 |

USD total = 50 + 120 + 50 − 20 = **200.00** → matches `control_totals_pass.csv` (`direct,200.00`).
`bad_rows.sql` adds order **1005 = −42.00 USD, is_return false** (the row DQ quarantines).
Customer 4 is `is_deleted = true` — staging drops it (shows soft-delete handling).
FX rates live in `tests/fixtures/fx/sample.json` (`GBP 0.78`, `CAD 1.36` per USD).

### If someone asks "is this the real pipeline?"

No — it's the **walking skeleton**: one source (`oltp` + `fx`), ~10 transforms, 3 of the
8 reconciliation checks, plain DuckDB SQL instead of dbt, a Python loop instead of
Dagster. Same table names, same column names, same gate behaviour as the real
build, so the SQL lifts into `dbt/models/**` almost verbatim. See the mapping table below.

## Files

| Path | Role |
|------|------|
| `demo/load.py` | fixtures → `bronze.*` in a fresh `.local_state/demo.duckdb` (also used by `tests/conftest.py`) |
| `demo/sql/10_staging.sql`, `20_marts.sql` | the transforms as plain DuckDB SQL (become `dbt/models/**` bodies in the real build) |
| `demo/checks.py` | the 3 reconciliation checks (`CheckResult` shape) |
| `demo/run.py` | the orchestrator: load → transform → DQ → reconcile → publish/block |
| `tests/fixtures/oltp/{sample,bad_rows,bad_rows_fixed}.sql` | the `good` / `bad` / `fixed` datasets |
| `tests/fixtures/recon/control_totals_{pass,fail,fixed}.csv` | the reconciliation source-of-truth totals |
| `tests/unit/test_demo.py` | 7 real tests over the slice (the buildsheet stub tests are still `skip`) |

## The same slice, as real dbt models

The `demo/sql/*.sql` logic is now also implemented as proper **dbt models** —
tagged `slice` — so you can run it through dbt on DuckDB exactly as production
runs it on Databricks:

```bash
make dbt-ci            # loads fixtures as bronze.* -> dbt deps -> dbt build --select tag:slice --target ci
```

| dbt object | file |
|------------|------|
| sources | `dbt/models/staging/oltp/_oltp__sources.yml`, `.../fx/_fx__sources.yml` (`bronze.oltp__*`, `bronze.fx__rate`) |
| staging | `stg_oltp__customers` (hashes email, drops soft-deletes), `stg_oltp__orders`, `stg_oltp__order_lines`, `stg_fx__rate` |
| intermediate | `int_sales__orders_usd` (currency → USD via the `to_usd` macro) |
| marts | `dim_fx_rate`, `dim_customer` (hashed email only), `fct_order`, `fct_order_line` (both `incremental`+`merge`), `reject__fct_order` (the DQ03 quarantine) |
| seeds | `control_totals.csv` (reconciliation source-of-truth), `currency_list.csv` |
| generic tests | `not_null` / `unique` / `relationships` + `dbt_expectations` regex on `email_hash` + a `min_value=0` guard on `fct_order.net_amount_usd where is_return=false` (DQ03) |
| singular recon tests (`tag:recon`) | `recon_row_counts`, `recon_gmv_control_total` (uses `var('recon_tolerance_pct')`), `assert_order_equals_lines`, `assert_no_pii_in_gold` |

`make demo` (Python/DuckDB) and `make dbt-ci` (dbt/DuckDB) produce the **same
`gold.fct_order`** from the same fixtures — one is the zero-dependency
walking-skeleton, the other is the real transformation code.

## How this maps to the real pipeline

| Demo | Production |
|------|-----------|
| `demo/load.py` | the 6 `extractors/` + `landing` writing Delta `bronze.*` |
| `demo/sql/*.sql` **and** the `tag:slice` dbt models | the full `dbt/models/**` on Databricks (`dbt-databricks`) |
| `reject__fct_order` (demo table / dbt model) | `silver` reject tables + the Elementary DQ report |
| `demo/checks.py` + `run.py` gate / the `tag:recon` singular tests | `recon/gate.py` + the **blocking** Dagster `@asset_check` |
| `gold.fct_order` + `_SUCCESS` | `publish` / `catalog_register` assets, watermark advance |

The other ~29 dbt models (shopify / pos / ga4 / salesforce, snapshots, the other
marts) and the `extractors/`, `recon/`, `publish/`, `northwind_dagster/`, `infra/`
bodies are still scaffold — implement them against the buildsheets in `../build/`,
following the `tag:slice` models as the worked example.
