# Component design

> One section per component from the architecture overview inventory. Keep each
> to responsibility / interfaces / config / failure modes / idempotency.

## Template per component

### `<component name>`

- **Responsibility:** one sentence - what it owns, what it does not.
- **Triggered by:** orchestrator task / upstream component / event
- **Inputs:** datasets, config files, parameters, state read
- **Outputs:** datasets, markers, metrics, state written, lineage events
- **Configuration:** what is configurable, where it lives, per-environment overrides
- **Key logic / algorithm:** the 3-6 steps it performs
- **Failure modes & handling:**

  | Failure | Detection | Response |
  |---------|-----------|----------|
  | | | |

- **Idempotency:** how a re-run with the same inputs is safe
- **Scaling knobs:** parallelism, batch size, rate limits
- **Open questions:** (link Q# from Phase 1)

---

## Components to cover

1. Extractor (per source type: sql / csv / bigquery / api / ...)
2. Landing writer (atomic commit, manifest, markers)
3. Transformer / dbt runner (`dbt build`: models, snapshots, seeds; layer
   selectors; target per env; slim-CI state comparison)
4. DQ engine (dbt tests + engine rules, row routing, metrics)
5. Reconciliation engine (metric gather, evaluate spec, report, gate)
6. Loader (staging -> target per load pattern)
7. Orchestration (DAG, schedule, retry, backfill)
8. Lineage / metadata / catalog registration (run manifests + dbt `manifest.json`)
9. Secrets & security (reference resolution, masking, encryption)
10. Observability (logging, metrics, alerting)
11. State store (run registry, watermarks)
12. IaC / provisioning (Terraform modules, providers, state backend, drift check)
13. CI/CD deploy (lint / validate / plan / apply / `dbt build` / promote gates)

Fold 3/4 into the dbt runner where the project is ELT-on-warehouse; keep them
separate components only if transforms also run outside dbt. Cover 12/13 briefly
and point at `deployment-and-iac.md` for the detail.
