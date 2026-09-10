# project2

Subscription revenue analytics: **extract → dbt transforms → data-quality + reconciliation gate → publish**.
Built by the `lite_etl` harness from `../spec.md` + `../design.md`. Full runbook: `../DEMO.md`.

## Setup

Needs **Python 3.10+** and **PyYAML** only.

    python -m venv .venv
    .venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
    pip install -r requirements.txt
    pip install -r requirements-dbt.txt   # optional, only for the dbt slice

## Run it (no cloud)

    python -m demo.peek inputs         # BEFORE: source recipe, rules.yml, finance control total
    python -m demo.run                 # clean run  -> every check passes -> writes .local_state/gold/
    python -m demo.peek                # AFTER:  row counts, MRR, reconciliations, published gold/

    python -m demo.run --scenario fail # bad data -> rows quarantined + MRR identity BLOCKS publish, exit 1
    python -m demo.peek                # AFTER:  reject_fct_invoice populated, gold/ absent

(`make demo` / `make demo-fail` do the same if you have `make`.)

### What to check where

| when | command / path | shows |
|------|----------------|-------|
| before | `python -m demo.peek inputs` | the synthetic-source recipe (`demo/load.py`), `demo/data/control_totals.csv`, `rules.yml` |
| after (either run) | `python -m demo.peek` | `raw_* → stg_* → dim_/fct_` row counts, `reject_fct_invoice` rows, MRR by month, current-month movements, both reconciliations, `.local_state/gold/` listing |
| after (clean) | `.local_state/gold/{dim_account,dim_plan,fct_invoice,fct_mrr_movement}.csv`, `_SUCCESS` | published marts — USD amounts, no raw email / company name |
| after (fail) | `.local_state/gold/` | absent — publish was blocked |
| any time | `.local_state/demo.sqlite` | the full local warehouse; query any layer with a SQLite client |

## What's here

| path | what |
|------|------|
| `demo/` | the runnable pipeline on stdlib **SQLite** — `load.py` (synthetic sources), `sql/` (transforms), `rules.py` (runs `rules.yml`), `run.py` (orchestrates), `peek.py` (inspect in/out) |
| `rules.yml` | 5 quality checks + 2 reconciliations (revenue vs finance GL; MRR movement identity) — `warn` / `quarantine` / `fail` / `block` |
| `dbt/` | the **same transform SQL** as real dbt models (staging + `dim_account`/`dim_plan`/`fct_invoice` real; `fct_mrr_movement` stubbed), DuckDB `ci` target + Databricks / Snowflake targets |
| `dbt/macros/to_sha256.sql` | the thin per-engine seam |
| `infra/` | Terraform: one module, `envs/dev` + `envs/prod`; `engine` variable = `duckdb \| databricks \| snowflake` |
| `.github/workflows/ci.yml` | demo (clean + fail) · dbt · `terraform validate` |

## The point

The demo runs on SQLite so it starts anywhere. The dbt models and `rules.yml` are unchanged when
`infra` points `engine` at Databricks or Snowflake — only the connection profile differs.
The MRR movement reconciliation is an *internal identity* (`closing = opening + Σ movements`); the
`--scenario fail` run simulates a churn-detection bug and the gate catches it even though the
external revenue check still passes.
