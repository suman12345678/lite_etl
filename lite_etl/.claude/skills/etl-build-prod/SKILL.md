---
name: etl-build-prod
description: Phase 3 (prod, all-in-one). Scaffold projects/<active>/repo/ complete in one pass — runnable local demo AND full production code (real extractors for every source, full dbt models for every target table, real infra, real orchestration). Standalone — does not require etl-build to have run first.
---

# etl-build-prod

1. Read `spec.md` + `design.md` (path in `state/active`). Missing design → tell the user to run
   `/etl-design` first, stop.
2. Scaffold `repo/` completely, in one pass — no separate `/etl-build` step needed:
   - `demo/` — **runs on DuckDB/SQLite, no cloud.** `load.py` (synthetic fixtures → tables),
     `sql/` (transforms; these double as the dbt model bodies), `rules.py` (reads `rules.yml`,
     applies `warn`/`quarantine`/`fail`/`block`), `run.py` (load → transform → rules → publish
     `gold`, or block + exit 1), with a clean and a fail scenario. Real, small bodies.
   - `extract/` — one real module per source group in the spec's Sources table (e.g.
     `extract/billing.py`, `extract/crm.py`, `extract/ref.py`). Real client code: REST calls with
     pagination + incremental-by-`updated_at` where Sources says incremental, full-snapshot pulls
     where it says full, file reads for CSV/S3 sources. Each module writes rows into `raw.*` tables
     of the chosen engine. Host/token/connection-string values come from `os.environ` only — never
     a literal.
   - `dbt/models/` — full models for **every** entry in Target's model list (every staging model,
     every dim, every fact) — not one slice. Real SQL implementing every line in Transforms, with
     a `duckdb` `ci` target so `dbt build --target ci` runs with no cloud.
   - `rules.yml` — from the spec's Rules section, real config (quality + reconciliation).
   - `infra/` — real Terraform resources per engine: one module + `envs/<env>` per spec, actual
     provider blocks (warehouse/schema/compute, landing storage, the scheduled jobs for every
     cadence in Schedule) — not a `terraform_data` placeholder. Values flow through `var.*` /
     tfvars — never inline an account id, ARN, or secret.
   - `orchestration/` — a real job definition (cron / Airflow / GitHub Actions — match what
     design.md's Approach names) for every cadence in Schedule, not just prose.
   - `.github/workflows/ci.yml` — lint · `make demo` · `make demo-fail` · `dbt build --target ci`
     (full model set) · extractor unit tests against recorded fixtures (CI has no live creds) ·
     `terraform validate`.
   - `Makefile` — `demo`, `demo-fail`, `test`, `dbt-ci`, one `extract-<source>` target per source
     group, and `deploy`.
   - `README.md` — how to run the demo (20 lines, as etl-build); plus which env vars / secrets
     each extractor needs and where they're read from; how to deploy.
3. Self-check, all of these before handing back:
   - `python -m demo.run` exits 0 and publishes; `python -m demo.run --scenario fail` exits 1
   - `python -m compileall demo extract`; every `.yml` / `.tf` parses
   - `dbt compile` (or `dbt build --target ci`) succeeds against the full model set
   - `terraform validate` passes
   - grep the whole repo for anything that looks like a literal secret, token, hostname, or
     account id — any hit is a failure, fix before handing back
4. Check every Sources / Target / Transforms / Rules / Schedule item in spec.md has **both** a
   demo implementation and a real (extract/dbt/infra) implementation. List any gap; don't hide it.
5. `progress.json` → `"phase": "build-prod"`. Point at `repo/README.md`.

Optional: run the `scaffolder-prod` agent for the bulk, then review.

Rules: real bodies everywhere — the demo slice, every source's extractor, every dbt model, and
infra. No stubs, no `TODO` placeholders for logic. No secrets, no real account ids/ARNs/hosts
anywhere, ever — always an env var, secrets-manager reference, or `var.*`. Keep demo numbers
internally consistent (FX rates, control totals reconcile) exactly as etl-build does.
