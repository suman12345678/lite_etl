# retail_demo

A tiny end-to-end retail order pipeline: **extract → dbt transforms → data-quality + reconciliation gate → publish**.
Built by the `lite_etl` harness from `../spec.md` + `../design.md`.

## Setup

The demo needs only **Python 3.10+** and **PyYAML**. Either use your system Python (if it
already has PyYAML) or make a venv:

    python -m venv .venv
    .venv\Scripts\activate            # Windows  (source .venv/bin/activate on macOS/Linux)
    pip install -r requirements.txt

    # optional, only for the dbt slice:
    pip install -r requirements-dbt.txt

With the venv active, `python ...` below uses it. Without activating, prefix commands with
`.venv\Scripts\python` (or pass `PY=.venv/Scripts/python` to `make`).

## Run it (no cloud)

    python -m demo.peek inputs         # check BEFORE: source recipe, rules.yml, finance control totals
    python -m demo.run                 # clean run  -> every check passes -> writes .local_state/gold/
    python -m demo.peek                # check AFTER:  row counts, quarantine, reconcile, published gold/

    python -m demo.run --scenario fail # bad data   -> rows quarantined + reconcile BLOCKS publish, exit 1
    python -m demo.peek                # check AFTER:  reject_fct_order populated, gold/ absent

(`make demo` / `make demo-fail` do the same run if you have `make`.)

### What to check where

| when | command / path | shows |
|------|----------------|-------|
| before | `python -m demo.peek inputs` | the synthetic-source recipe (`demo/load.py`), `demo/data/control_totals.csv`, `rules.yml` |
| after | `python -m demo.peek` | `raw_* → stg_* → marts` row counts, `reject_fct_order` rows, per-channel pipeline-vs-finance, `.local_state/gold/` listing |
| after (clean) | `.local_state/gold/fct_order.csv`, `dim_customer.csv`, `_SUCCESS` | published marts — USD amounts, no raw email |
| after (fail) | `.local_state/gold/` | absent — publish was blocked |
| any time | `.local_state/demo.sqlite` | the full local warehouse; query it with any SQLite client |

## What's here

| path | what |
|------|------|
| `demo/` | the runnable pipeline on stdlib **SQLite** — `load.py` (synthetic sources), `sql/` (transforms), `rules.py` (runs `rules.yml`), `run.py` (orchestrates), `peek.py` (inspect in/out) |
| `rules.yml` | data quality + reconciliation in one file — `warn` / `quarantine` / `fail` / `block` |
| `dbt/` | the **same transform SQL** as real dbt models, with a DuckDB `ci` target and Databricks / Snowflake targets stubbed |
| `dbt/macros/to_sha256.sql` | one example of the thin per-engine seam |
| `infra/` | Terraform: one module, `envs/dev` + `envs/prod`; the `engine` variable = `duckdb \| databricks \| snowflake` |
| `.github/workflows/ci.yml` | demo (clean + fail) · dbt · `terraform validate` |
| `DEMO.md` | the two-minute script to run on stage |

## The point

The demo runs on SQLite so it starts anywhere. The dbt models and `rules.yml` are unchanged when
`infra` points `engine` at Databricks or Snowflake — only the connection profile differs.
