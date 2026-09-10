# northwind-data (scaffold)

Starter repo scaffolded by the lite-etl-design harness, Phase 3
(`/build-components`) from `../../design/`. **Stubs only** - every model body
and extractor `run()` is a `TODO`. See `../build-plan.md` for the build order
and one buildsheet per component.

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

Phase 4 (`/assemble-pipeline`) adds `infra/`, `dagster/`, `.github/workflows/`.

## Local

`make setup` then `make test`. See `../local-dev.md`.
