# Architecture diagram

> Mermaid. One readable screen. Replace the skeleton with the real components,
> source types, and target from the requirements. Label edges with what flows.

## System context

```mermaid
flowchart LR
  subgraph Sources
    S1[(SQL DB)]
    S2[/CSV drop/]
    S3[(BigQuery)]
    S4([REST API])
  end

  subgraph Harness["ETL data harness"]
    EX[Extract\nper source type] --> LZ[[Landing zone\nraw, immutable]]
    LZ --> TF[Transform\ncleanse / standardise / historise]
    TF --> DQ{Data-quality\nrules}
    DQ -->|pass| CU[[Curated staging]]
    DQ -->|reject| QZ[[Quarantine\n+ reason codes]]
    CU --> RC{Reconciliation\ngate}
    RC -->|PASS| LD[Load\nper load pattern]
    RC -->|FAIL| AL
    LD --> TGT[(Target warehouse\n/ lakehouse)]
  end

  subgraph Control["Orchestration & observability"]
    OR[Orchestrator] -.triggers.-> EX
    OR -.triggers.-> TF
    OR -.triggers.-> LD
    MET[Metrics / logs / lineage] -.collects.-> Harness
    AL[Alerting] -.on failure / SLA breach.-> ONCALL[On-call]
  end

  subgraph Deploy["Build & deploy plane"]
    GIT[(Git repo)] --> CI[CI/CD: lint / validate / plan]
    CI -->|merge| TFA[terraform apply\nwarehouse objects, grants, compute, storage]
    CI -->|merge| DBT[dbt build\nmodels + tests + snapshots]
    TFA -.provisions.-> Harness
    DBT -.deploys models to.-> TF
  end

  S1 --> EX
  S2 --> EX
  S3 --> EX
  S4 --> EX
  MET --> CAT[(Catalog / metadata)]
```

## Notes

- **Zones:** landing = exact source bytes/rows; curated staging = post-transform,
  pre-publish; target = consumer-facing.
- **The reconciliation gate is hard:** a FAIL never writes `_SUCCESS` and never
  publishes to the target.
- **Two planes, two cadences:** the data pipeline runs on a schedule; the build &
  deploy plane runs on a git merge. `terraform apply` provisions the harness's
  infrastructure; `dbt build` ships the transformation models. Detail in
  `deployment-and-iac.md` and `transformation-design.md`.
- Adjust source nodes to the actual set in `01-source-systems.md`; drop planes
  that requirements put out of scope.
