# retail_demo — the two-minute script

Goal for the audience: *this harness turns a short spec into a real, gated ETL pipeline,
and the same pieces run on Databricks / Snowflake / DuckDB.*

Two helper commands do all the "look here" work:

    python -m demo.peek inputs    # what goes IN  (source recipe, rules.yml, finance totals)
    python -m demo.peek           # what came OUT (row counts, quarantine, reconcile, gold/)

---

## 0. Before you start (10 sec)

Show the two files the harness worked from — `../spec.md` (the interview) and `../design.md`
(every component names the spec line it satisfies). Then: "here's what it scaffolded."

## 1. Look at the inputs — BEFORE the run (20 sec)

```
python -m demo.peek inputs
```

It prints three things; call them out:

| shown | file | point to make |
|-------|------|---------------|
| source recipe | `demo/load.py` | deterministic synthetic `orders` / `customers` / `fx_rates`; note the planted quirks: `@example.test` test rows, a weekend gap in FX, a duplicate order re-send |
| finance control totals | `demo/data/control_totals.csv` | plain CSV, **editable on stage** — this is the number reconciliation checks against |
| the rules | `rules.yml` | data quality **and** reconciliation in one file; `on_fail: warn / quarantine / fail / block` |

(Raw tables don't exist yet — `load.py` builds them into `.local_state/demo.sqlite` at run time.)

## 2. Clean run — the happy path (30 sec)

```
python -m demo.run
```

Talk over the four stages it prints: **LOAD** (`raw.*`) → **TRANSFORM** (`raw → staging → marts`;
note *"dropped 3 test-email customers; deduped 1 resent order"*) → **RULES GATE** (4 quality checks
`ok`, `reconcile: pipeline == finance`) → **VERDICT** (`published gold/` + `_SUCCESS` + watermark).

### Check the outputs — AFTER the run

```
python -m demo.peek
```

- **Row counts** — `raw_* → stg_* → dim_/fct_`; `raw_orders 211 → stg_orders 210` is the dedupe.
- **Per-channel net_usd** — pipeline vs finance, all `diff 0.00%`.
- **Published artifacts** — `.local_state/gold/dim_customer.csv`, `fct_order.csv`, `_SUCCESS`.

Then open one file: `type .local_state\gold\fct_order.csv` (Windows) / `cat .local_state/gold/fct_order.csv` —
money is in USD, and there is no email column anywhere.

## 3. Bad data — the gate earns its keep (45 sec)

```
python -m demo.run --scenario fail
```

Two independent things go wrong, and the pipeline reacts differently to each:

- **Quality → quarantine.** Three refund rows arrived with negative totals. The
  `net_usd_non_negative` rule moves them to `reject_fct_order` and the run *continues*.
- **Reconciliation → block.** Finance's `web` control total is 12% off the pipeline's number.
  `> 0.5%` tolerance ⇒ **PUBLISH BLOCKED**, `gold/` not written, **exit 1**.

### Check the outputs — AFTER the failed run

```
python -m demo.peek
```

- **`reject_fct_order`** section now lists the 3 quarantined rows + the rule that caught them.
- **Per-channel net_usd** — `web` now shows `diff 10.71%` against the control total the run used.
- **Published artifacts** — *"(none — the run was BLOCKED, nothing published)"*. `gold/` is absent.

"A schema-valid but *wrong* load never reaches consumers."

## 4. Any warehouse (20 sec)

- `dbt/models/` — the exact same SQL as `demo/sql/`, as real dbt models. `dbt/profiles/profiles.yml`
  has `ci` (DuckDB), `databricks`, `snowflake` targets. `dbt/macros/to_sha256.sql` is the whole
  per-engine difference.
- `infra/` — Terraform. `infra/envs/prod/prod.tfvars` is one line: `engine = "snowflake"`.
  Flip it to `"databricks"` — no model changes.

Close: "Same spec, same gate, same tests — Databricks, Snowflake, or your laptop."

---

### Reset between runs
Nothing to reset — each run rebuilds `.local_state/` from scratch. `make clean` removes it.
