# Architecture overview - Meridian Trust Regulatory & Risk Data Harness (DEMO)

> Phase 2 deliverable. Written by the `design-etl-architecture` skill
> (`/design-architecture`) on 2026-09-03 from `../requirements/`.
> Every choice carries a "because <requirement>". Fictional client.

- **Project:** Meridian Trust - Regulatory & Risk Data Harness
- **Date / version:** 2026-09-03 / v1
- **Requirements baseline:** `../requirements/` v1.1 (post `/finalize-requirements`)

## 1. Approach

- **ETL vs ELT:** **mixed / split.**
  - ETL in Python for extraction, file parsing, decoding, **PAN reduction and PII
    tokenisation**, minor-unit conversion, structural validation - *because*
    `08` requires full PAN to never persist and PII to be tokenised **before**
    it reaches Snowflake, and `03` puts parsing/decoding of the fixed-width card
    file outside SQL's comfort zone.
  - ELT in **dbt on Snowflake** for joins, SCD2, currency conversion, the
    dimensional model and DQ/recon SQL - *because* `00`/`09` say the team knows
    dbt+SQL and prefers set-based work in the warehouse they've paid for.
- **Processing style:** **T+1 daily batch** for all sources - *because* `00`/`09`
  put real-time explicitly out of scope; card landing path is kept
  file-count-agnostic for a possible future intraday move (`99` Q3).
- **Zone model:** `S3 landing` → `RAW` → `STAGING` → `CURATED` (+ `CURATED_SENSITIVE`)
  - *because* `02` requires an immutable landing tier and `06`/`08` require a
    governed, access-controlled curated tier with sensitive data segregated.
- **Orchestration:** **Airflow on Amazon MWAA** - *because* `07` names it and the
  team's skills + managed-service preference in `00`.
- **Storage & formats:** Parquet (Snappy) in S3; Snowflake tables clustered by
  `business_date` (facts) / business key (dims) - *because* `02` layout + `09`
  cost controls (pruning).
- **Idempotency & replay:** `run_id` per `(source, business_date)`; facts delete
  prior rows for the date before insert; dims re-derive SCD2 from the latest
  snapshot; watermark advances only after recon PASS + publish - *because* `00`
  ("re-run produces identical output") and `02`.

## 2. Component inventory

| Component | Responsibility | Technology | Because (requirement) |
|-----------|----------------|------------|-----------------------|
| Source extractors (×5) | pull each source to S3 landing (Parquet + manifest) | Python 3.11, PyArrow; connectors: Oracle, SFTP, BigQuery, REST, SQL Server | 01 |
| Card file parser | decode Win-1252, strip header/TOTAL, fixed-width amount, drop full PAN, keep last 4 | Python (part of the card extractor) | 01, 03, 08 |
| PII tokeniser | FPE tokenise name/DOB/national-id/address before landing; write real values to the `CURATED_SENSITIVE` load path only | Python + Vault-managed keys | 08 |
| Landing writer | atomic S3 write, `manifest.json`, `rejects.parquet`, `_SUCCESS` | Python | 02, 06 |
| Schema-drift check | compare landed schema to the registered contract; fail/warn | Python + DataHub schema | 06 |
| RAW loader | copy landing Parquet into `RAW.<source>__<object>` | Snowflake `COPY INTO` / external tables | 02 |
| Transform + model | STAGING cleanse, SCD2, FX conversion, dimensional build | dbt-snowflake | 03 |
| DQ engine | run rule set per feed, route rows pass/quarantine/reject, emit `_dq_report.json` + `DQ_DAILY` | dbt tests + a small Python rule runner for row-level quarantine | 04 |
| Reconciliation engine | gather source/landing/curated metrics, evaluate the spec, emit `_reconciliation.json`, set/deny the publish gate | Python + Snowflake SQL | 05 |
| Publisher | single-transaction swap of the business date into `CURATED`; `_SUCCESS`; advance watermark | dbt + Python | 02, 05 |
| Orchestration | per-source DAGs, `curated_build` DAG, sensors, retries, backfill | Airflow / MWAA | 07 |
| Lineage & catalog | manifests → `RUN_MANIFEST`; OpenLineage from ETL + dbt → DataHub | OpenLineage, DataHub | 06 |
| Secrets & security | resolve `awssm://` / `vault://` refs; KMS; row-access policies | AWS Secrets Manager, Vault, Snowflake policies | 08 |
| Observability | structured logs, metrics, "Risk Data health" dashboard, alert routing | CloudWatch, Airflow, Grafana/QuickSight, PagerDuty, Slack | 07, 09 |
| Pipeline state | watermarks, run registry | `CURATED.PIPELINE_STATE` (Snowflake) | 02, 09 |

## 3. Environments

Three isolated AWS accounts + three Snowflake accounts (`_DEV`, `_UAT`, `_PRD`).
All infra in Terraform, all code/dbt/config in Git, promoted by tagged release
via GitHub Actions (`09`). dev = synthetic subset; uat/prod = real source
replicas (`99` Q5, assumed). UAT exercises the tokenisation and erasure paths
(`08`, `99` Q4).

## 4. Cross-cutting concerns

- **Data quality:** row-level rules in the Python runner at STAGING (quarantine
  to `rejects.parquet` + `STAGING.*_QUARANTINE`); set-level assertions as dbt
  tests. Thresholds from `04` (0.1% regulated / 0.5% card / GL zero-tolerance).
- **Reconciliation:** runs after STAGING, before publish. Hard FAIL ⇒ no
  `_SUCCESS`, no `CURATED` swap, Airflow task fails, business date stays open.
  Sub-ledger↔GL tie-out is warn-only initially (documented breaks expected).
- **Lineage:** every curated row carries `_source_run_id`, `_loaded_at`,
  `_dbt_invocation_id`; OpenLineage graph in DataHub; manifests retained 7 years.
- **Security:** full PAN dropped in memory in the parser; PII tokenised
  pre-landing; real PII only in `CURATED_SENSITIVE` behind a row-access policy;
  SSE-KMS + Tri-Secret Secure (prod); least-privilege role per source.
- **Observability:** one health dashboard; PagerDuty Sev2 for SLA/recon/DQ-block;
  Slack for warnings, drift, FX carry-forward, quarantine growth.

## 5. Open design assumptions (from `../requirements/99-open-questions.md`)

| Ref | Assumption the design makes | Impact if wrong |
|-----|-----------------------------|-----------------|
| Q1 | BCBS 239 mandatory set = discovery draft list; other fields nullable+flagged | non-null constraints and completeness rules in `CURATED` change; model columns may need `not_null` tests added |
| Q3 | Cards stay daily-file for 12+ months; landing path is file-count-agnostic but scheduling is daily | if intraday arrives, `card_transactions_daily` becomes micro-batch; `FACT_CARD_TXN` load already append+dedup so low blast radius |
| Q5 | dev on synthetic subset; uat/prod on real replicas | if dev must use real data, extra masking + access work in the dev account |

## 6. Out of scope

Real-time/intraday; the regulatory calculation engine; source-system changes;
BI/dashboards on `CURATED`. (`00`)
