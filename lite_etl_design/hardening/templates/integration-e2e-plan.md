# Integration & end-to-end plan

> Phase 5 deliverable. The scenarios that test real components together and the
> whole pipeline through a business date.

- **Dev env used:** (from `pipeline/environments-and-config.md`)
- **Isolation:** dedicated test schema / catalog per run, dropped after

## Integration scenarios (2-3 components, real warehouse + storage)

| # | Components | Scenario | Asserts |
|---|-----------|----------|---------|
| I1 | extractor + landing writer | extract `<src>` sample -> land | rows in `bronze`, manifest written, markers, `_run_id` |
| I2 | landing + dbt staging | land then `dbt build --select stg_<src>__*` | staging rows match golden |
| I3 | dbt marts + reconciliation | build `gold` for the golden date + `dbt test --select tag:recon` | recon PASS, `_reconciliation.json` shape |
| I4 | reconciliation + loader | force a recon FAIL fixture | publish does NOT run, non-zero exit, alert stub called |
| I5 | secrets resolver + extractor | missing secret ref | fails fast with a clear error, no partial land |

## Contract tests

| # | Contract | Scenario | Asserts |
|---|----------|----------|---------|
| C1 | source schema (`sources.yml`) | add/remove/retype a column in a fixture | drift check fires per policy |
| C2 | `gold` output schema | snapshot `gold.*` columns + types | breaking change fails CI until the consumer-notice label is set |
| C3 | consumer contract | the exposures in `transformation-design.md` s.9 still resolve | `dbt ls --select exposure:*` clean |

## End-to-end scenarios (whole pipeline, orchestrator run in dev)

| # | Scenario | Setup | Asserts |
|---|----------|-------|---------|
| E1 | happy golden day | full synthetic day for every source | `gold` matches golden, recon PASS, published, watermark advanced, SLA met |
| E2 | one source late | hold `<src>` file past its deadline | pipeline waits / alerts per `07`, does not publish a partial day |
| E3 | DQ over threshold | inject bad rows > fail threshold in `<src>` | run fails, nothing publishes, reject table populated |
| E4 | reconciliation break | control total off by > tolerance | publish blocked, alert, run non-zero |
| E5 | re-run same day | run E1 twice | identical output, no double count, watermark advances once |
| E6 | backfill window | run 3 past business dates oldest-first | each reconciles independently, correct final state |
| E7 | rollback | publish a bad day (bypass gate in test), then run the rollback procedure | `gold` restored, runbook steps accurate |

## Stubbed vs real

| Dependency | Integration | E2E |
|------------|-------------|-----|
| source APIs / DBs | fixtures / mock | recorded full-day or synthetic |
| warehouse | real (dev) | real (dev) |
| object storage | real (dev bucket) | real (dev bucket) |
| orchestrator | direct calls | real orchestrator run |
| alerting / paging | captured stub | captured stub |

## Runtime budget

Integration < `<x>` min (PR-blocking) or nightly if longer. E2E nightly +
before every promotion.
