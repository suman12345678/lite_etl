# Orchestration wiring

> Phase 4 deliverable. How the Phase 3 components become runnable pipelines on
> the orchestrator chosen in `requirements/07` / `design/pipeline-blueprint.md`.
> Keep the DAG shape from the design; this file is the wiring detail.

- **Orchestrator:** Airflow / Dagster / Prefect / Databricks Workflows / ...
- **Deployment:** how pipeline code is deployed (image / code-location / bundle)
- **Repo path:** `<orchestrator>/` - `dags/` (Airflow), `<project>_dagster/`
  (Dagster - **never a bare `dagster/`**, it shadows the library), `flows/` (Prefect)

## Pipeline: `<name>`

| Design task | Component / call | Orchestrator unit | Config |
|-------------|------------------|-------------------|--------|
| plan / resolve watermark | `extractors.<src>.plan` | task/asset `plan` | `--date`, watermark from state store |
| extract | `extractors.<src>.run` | task/asset `extract_<src>` | retries 3 / expo |
| land raw | `landing.write` | task/asset `land_<src>` | new `run_id` |
| schema-drift check | `dq.schema_check` | task/asset `schema_<src>` | policy fail/warn/evolve |
| transform | `dbt build --select <sel> --target <env>` | task/asset `dbt_build` | threads, cluster |
| DQ | (part of `dbt build`) | - | thresholds from `04` |
| reconcile | `dbt test --select tag:recon` + `recon.compare` | **blocking check / short-circuit** `reconcile` | tolerances from `05` |
| load / publish | `loader.publish` | task/asset `publish` (only if reconcile PASS) | txn per business date |
| finalize | `lineage.emit` + advance watermark | task/asset `finalize` | writes state store |

## Triggers

- **Schedule:** `<cron>` (per pipeline, from `07`)
- **Sensors / events:** `<file-arrival / upstream dataset / API>`
- **Dependencies:** `<pipeline X must be fresh before this runs>`

## Cross-cutting

- **Retry policy:** transient `<n>/<backoff>`; permanent = stop + alert (from `07`).
- **The reconciliation gate:** `reconcile` failure => `publish` never runs, run
  exits non-zero, no `_SUCCESS`, watermark unchanged, alert fires.
- **Backfill entrypoint:** `<command / params>` - re-runs a `[from, to]` window,
  one `run_id` per business date, oldest first (from `pipeline-blueprint.md`).
- **Concurrency:** max parallel runs; per-partition parallelism.
- **Alert routing:** channel + who, per trigger (from `07`).

## Skeleton files to scaffold

```
<orchestrator>/
  <pipeline>.py            # DAG / @job / flow - tasks above, wired, retries set, gate as short-circuit
  resources.py|config      # connections to warehouse / storage / secrets (refs only)
  schedules.py sensors.py
  backfill.py              # the backfill entrypoint
```

Stubs: correct structure, task names, dependency edges, retry config, the gate.
`TODO` for anything the design does not pin down.
