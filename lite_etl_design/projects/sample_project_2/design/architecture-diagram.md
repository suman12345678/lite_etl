# Architecture diagram - Northwind Commerce (DEMO)

> Mermaid. System context: 6 sources -> extractors -> Databricks lakehouse
> (bronze/silver/gold) -> reconciliation gate -> gold -> consumers, with the
> Dagster control plane and the Terraform + GitHub Actions build/deploy plane.

## System context

```mermaid
flowchart LR
  subgraph Sources
    S1[(Postgres OLTP)]
    S2([Shopify Admin API])
    S3[/POS CSV.gz on S3/]
    S4([Salesforce Bulk API])
    S5[(GA4 in BigQuery)]
    S6([FX rates API])
  end

  subgraph Harness["Northwind data harness - Databricks lakehouse"]
    EX[Extractors\nPython + BigQuery job] --> BZ[[bronze\nDelta, immutable, _run_id]]
    BZ --> ST[silver\ndbt staging + intermediate\ncleanse / dedupe / FX / identity]
    ST --> DQ{dbt tests\nDQ rules}
    DQ -->|pass| GLD[[gold marts\ndbt: dims via snapshots, incremental facts, aggs]]
    DQ -->|reject| QZ[[silver reject tables\n+ reason_code]]
    GLD --> RC{reconcile\nrow counts / GMV / refunds / PII-leak}
    RC -->|PASS| PUB[publish + UC register]
    RC -->|FAIL| AL
    PUB --> GC[(gold + gold_pii\nUnity Catalog)]
  end

  subgraph Control["Dagster (Cloud hybrid, ECS agent)"]
    OR[Asset graph + schedules + S3 sensor] -.materialise.-> EX
    OR -.materialise.-> ST
    OR -.asset check.-> RC
    MET[Elementary + CloudWatch + system tables] -.collect.-> Harness
    AL[PagerDuty / Slack] -.SLA breach / recon FAIL.-> ONCALL[AE on-call]
  end

  subgraph Deploy["Build & deploy plane"]
    GIT[(GitHub mono-repo)] --> CI[GitHub Actions\nlint / validate / plan / slim dbt build]
    CI -->|merge to main| TFA[terraform apply\nUC catalogs+grants, storage+KMS, Dagster ECS agent, GA4 SA, alarms]
    CI -->|merge to main| DBT[dbt build --target env\n+ dagster deploy]
    CI -->|manual approval| PROM[promote dev -> stg -> prd\nsame SHA + manifest]
    TFA -.provisions.-> Harness
    DBT -.deploys models to.-> ST
  end

  S1 --> EX
  S2 --> EX
  S3 --> EX
  S4 --> EX
  S5 --> EX
  S6 --> EX
  GC --> CONS[Looker / Braze reverse-ETL / Finance close]
  MET --> CAT[(dbt docs site + UC lineage + OpenLineage)]
```

## Notes

- **Zones:** `bronze` = exact source rows/bytes as landed (60-day retention);
  `silver` = dbt-transformed, DQ-checked, pre-publish; `gold` / `gold_pii` =
  consumer-facing, published only after reconcile PASS.
- **The reconciliation gate is hard:** implemented as a blocking Dagster asset
  check over singular dbt tests + a Python manifest compare. A FAIL means
  `publish` and `catalog_register` never materialise and the run exits non-zero.
- **Two planes, two cadences:** the data pipeline runs on Dagster schedules /
  the S3 sensor and must publish by 06:00 UTC; the build & deploy plane runs on
  a GitHub merge - `terraform apply` provisions infra, `dbt build` ships models,
  promotion is manual dev -> stg -> prd. See
  [`deployment-and-iac.md`](deployment-and-iac.md).
- **PII:** `silver` hashes email/phone; real values flow only into `gold_pii`,
  which UC governs with a row filter + column mask.
