# Build - Northwind Commerce (DEMO)

**One-line:** an ordered build plan + a buildsheet per component + a dbt project
scaffold doc + a fixtures catalog + a local-dev guide, and a scaffolded starter
repo under [`repo/`](repo/) - Python extractors for the 6 sources, the dbt
project (staging -> intermediate -> marts + snapshots + seeds + DQ tests), and
the reconciliation / publish / lineage / observability engines, all as stubs with
`TODO` bodies. Local tests run on DuckDB + mock HTTP + sample files - no cloud.

**Produced by:** the `build-etl-components` skill (`/build-components`) on
2026-09-09 from [`../design/`](../design/). Fictional client.

## Files

| File | Contents |
|------|----------|
| [build-plan.md](build-plan.md) | 9-component build order, "component complete" definition, local-run + CI hook, open items |
| [component-buildsheet-config.md](component-buildsheet-config.md) | config loader + `_state.watermarks` state store |
| [component-buildsheet-secrets.md](component-buildsheet-secrets.md) | `secret-scope://` resolver + PII hashing helper |
| [component-buildsheet-extractor.md](component-buildsheet-extractor.md) | the extractor framework + 6 source modules (oltp / shopify / pos / salesforce / ga4 / fx) |
| [component-buildsheet-landing.md](component-buildsheet-landing.md) | atomic Delta write, manifest, `_run_id` tagging, POS supersede |
| [component-buildsheet-dbt-runner.md](component-buildsheet-dbt-runner.md) | the `dbt build` wrapper + the build/test contract |
| [component-buildsheet-reconciliation.md](component-buildsheet-reconciliation.md) | `tag:recon` dbt tests + Python manifest compare + the PASS/FAIL gate |
| [component-buildsheet-publisher.md](component-buildsheet-publisher.md) | `gold`/`gold_pii` transaction, UC register, watermark advance |
| [component-buildsheet-lineage.md](component-buildsheet-lineage.md) | run manifest + dbt manifest + OpenLineage emitter |
| [component-buildsheet-observability.md](component-buildsheet-observability.md) | structured logging + metric emit points |
| [dbt-project-scaffold.md](dbt-project-scaffold.md) | the full `dbt/` tree + the model/test/snapshot/seed -> design-section map + macros |
| [fixtures-catalog.md](fixtures-catalog.md) | per source: sample / empty / late / duplicate / drift / bad-rows / partial fixtures + golden outputs + recon fixtures |
| [local-dev.md](local-dev.md) | prereqs, `make` targets, how each source is faked locally, the dev loop |
| [repo/](repo/) | the scaffolded starter repo (stubs + `TODO`s) |

## Status

Phase 3 **complete (scaffold)**. The 14 build docs are written and `repo/` is
scaffolded - 152 files that parse (`ast` on every `.py`, `yaml.safe_load` on
every dbt/config `.yml`). Every model body and extractor `run()` is a `TODO`:
implementing them against these buildsheets until `make test` is green is the
developer work that follows. 4 open items (O1-O4 in `build-plan.md`), 2 tied to
Q3/Q4.

Next: `/assemble-pipeline` (Phase 4) - Dagster asset graph, Terraform modules,
GitHub Actions, wiring `make test` into CI.
