# Demo harness — the runnable walking skeleton

> Phase 3 deliverable, written as `build/repo/DEMO.md` and backed by a `demo/`
> package. Purpose: make the scaffold **runnable and demoable on a laptop** with
> no cloud, no warehouse, no dbt and no orchestrator — so the team can *show*
> data loading, a DQ rule catching and quarantining a bad row, and the
> reconciliation gate passing / blocking. Everything else in `build/repo/` stays
> a stub; this is the one vertical slice with real (small) bodies.

## Scope

Pick **one** source (the simplest with a clean key and a numeric measure — often
the OLTP/relational one) plus whatever it needs to reconcile (e.g. an FX table, a
control-total file). Target:

- ~1 source, ~8-12 transforms, 2-3 of the reconciliation checks from `05`
- one DQ rule from `04` that can **quarantine** a row (e.g. `amount >= 0 unless
  is_return`, `not null`, `in accepted set`)
- runs in < 5 s on DuckDB

## Files to scaffold (under `build/repo/`)

```
demo/
  __init__.py
  load.py          # fixtures -> a fresh DuckDB file as bronze.<src>__<obj> (+ _run_id/_source_file/_extracted_at/_ingest_date)
                   #   MUST be importable by tests/conftest.py too (one loader, one bronze shape)
  sql/
    10_staging.sql # bronze.* -> stg_*   (plain engine SQL; becomes dbt/models/staging bodies later)
    20_marts.sql   # stg_* -> int_* -> dim_*/fct_* + reject__<entity> (the DQ quarantine table)
  checks.py        # the 2-3 reconciliation checks, returning the CheckResult shape from recon/gate.py
  run.py           # orchestrator: load -> transform -> print quarantine -> reconcile -> publish|block
DEMO.md            # how to run it + how each piece maps to the real pipeline
tests/
  conftest.py      # real: bronze_db / bronze_con fixtures via demo.load  (NOT raise NotImplementedError)
  unit/test_demo.py# real, passing assertions over the slice
  fixtures/<src>/{sample,bad_rows,bad_rows_fixed}.*     # real content
  fixtures/recon/control_totals_{pass,fail,fixed}.csv   # real content
```

Add `duckdb` (+ `pyyaml` if not present) to the project's runtime deps.

## `run.py` behaviour

```
python -m demo.run [--dataset good|bad|fixed] [--control-totals pass|fail] [--date <D>]
```

| Step | Prints |
|------|--------|
| 1. LOAD | each `bronze.*` table + row count |
| 2. TRANSFORM + DQ | runs `sql/10_*`, `sql/20_*`; lists rows quarantined into `reject__<entity>` with `reason_code` + rule id; count published |
| 3. RECONCILE | each check: `expected / actual / delta / tolerance / verdict`; writes `.local_state/_recon/dt=<D>/_reconciliation.json` (same shape as `recon/gate.py`) |
| 4. GATE | **PASS** -> write `gold.<fact>` + `_SUCCESS` marker + advance a local watermark; **FAIL** -> print "PUBLISH BLOCKED", `sys.exit(1)` |

Datasets: `good` = clean; `bad` = one row the DQ rule must quarantine (design the
numbers so the gate still PASSes because the bad row is excluded — that is the
"DQ protected gold" story); `fixed` = the bad row corrected at source (+ an
updated control total) so the re-run is green with nothing quarantined.
`--control-totals fail` points the GMV/amount check at a mismatched control file
to force a FAIL and prove the gate blocks.

## Task-runner targets

```
demo:        python -m demo.run --dataset bad  --control-totals pass   # quarantine + PASS + publish
demo-good:   python -m demo.run --dataset good
demo-fixed:  python -m demo.run --dataset fixed
demo-fail:   python -m demo.run --dataset bad  --control-totals fail   # blocked, exit 1
```

## Rules

- No PII, no real data, no secrets. Fake emails `@example.test`.
- The demo SQL is written so it can later be lifted into `dbt/models/**` almost
  verbatim (same table names, same column names as the buildsheets).
- `DEMO.md` ends with a table mapping each demo file to its production counterpart
  (`demo/load.py` -> the real extractors + landing; `demo/sql/*` -> dbt models;
  `demo/checks.py` + gate -> `recon/gate.py` + the blocking orchestrator check;
  `gold.*` + `_SUCCESS` -> the publish/register assets).
- `tests/unit/test_demo.py` must pass in CI; keep the other buildsheet stub tests
  `@skip("TODO")`.
