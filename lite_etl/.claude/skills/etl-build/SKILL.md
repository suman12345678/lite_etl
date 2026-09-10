---
name: etl-build
description: Phase 3. Scaffold projects/<active>/repo/ with a runnable local demo.
---

# etl-build

1. Read `spec.md` + `design.md`. Missing design → run `/etl-design` first, stop.
2. Scaffold `repo/`:
   - `demo/` — **runs on DuckDB, no cloud**. `load.py` (synthetic fixtures → tables),
     `sql/` (transforms; these double as the dbt model bodies), `rules.py` (reads `rules.yml`,
     runs each check, applies `warn`/`quarantine`/`fail`/`block`), `run.py`
     (load → transform → rules → publish `gold`, or block + exit 1). Real, small bodies.
   - `dbt/` — one vertical slice as real models (`sources.yml`, staging, one fact + one dim) with a
     `duckdb` `ci` target. Remaining models: stubs with `TODO`.
   - `rules.yml` — from the spec's Rules section.
   - `infra/` — Terraform: one module + `envs/<env>` per spec. `var` refs / `TODO` only, no real ids.
   - `.github/workflows/ci.yml` — lint · `make demo` · `dbt build --target ci` · `terraform validate`.
   - `Makefile` — `demo`, `demo-fail`, `test`, `dbt-ci`.
   - `README.md` — how to run, 20 lines.
3. Self-check: `python -m demo.run` exits 0 and publishes; `make demo-fail` exits 1;
   `python -m compileall demo`; every `.yml` parses. Fix before handing back.
4. `progress.json` → `"phase": "build"`. Point at `repo/README.md`.

Optional: run the `scaffolder` agent for the bulk, then review.

Rules: real bodies only for the demo slice + the dbt slice; stubs + `TODO` elsewhere.
No secrets, no real account ids. Keep the demo numbers consistent (FX, control totals line up).
