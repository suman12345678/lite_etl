# northwind-data (scaffold)

Starter repo scaffolded by the lite-etl-design harness, Phase 3
(`/build-components`) from `../../design/`. Most component bodies are still
`TODO` — see `../build-plan.md` for the build order and one buildsheet per
component.

**Want to see it work?** `make demo` — a real, runnable DuckDB slice
(load → data-quality quarantine → reconciliation gate → publish) with no cloud.
See [`DEMO.md`](DEMO.md).

```
extractors/   Python: 6 source modules + common/ (config, state, secrets, landing, manifest, base, http, dbt_runner)
recon/        reconciliation engine + PASS/FAIL gate
publish/      gold/gold_pii publisher + UC register
lineage/      run manifest + dbt manifest -> OpenLineage
obs/          structured logging + metric emit
dbt/          the dbt project (staging -> intermediate -> marts + snapshots + seeds + tests)
config/       defaults.yml + <env>.yml
tests/        unit/ + fixtures/ + golden/
```

Phase 4 (`/assemble-pipeline`) adds `infra/`, `northwind_dagster/`, `.github/workflows/`.
`demo/` is the runnable walking-skeleton slice (`make demo`).

## Local

`make setup` then `make test`. See `../local-dev.md`.
