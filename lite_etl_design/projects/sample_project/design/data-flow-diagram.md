# Data-flow diagram - Meridian Trust (DEMO)

> Produced by `/design-architecture` on 2026-09-03. One diagram per source shape.

## Card transactions - file-arrival

```mermaid
flowchart TD
  A[/"SFTP: CARDTXN_YYYYMMDD*.psv (1-2 parts)"/] -->|"S3 sensor / SFTP poll -> S3"| B["Card parser\nWin-1252, strip header + TOTAL line\nminor units /100, PAN -> last4"]
  B -->|"parsed rows + control totals"| C[["S3 landing\ncard/card_transactions/business_date=/run_id=/"]]
  C --> D{"Schema drift vs contract?"}
  D -->|no| E["RAW.card_transactions__txn"]
  D -->|yes| X["Halt + DataHub ticket + Slack"]
  E --> F["STAGING: dedupe (txn_id, post_date)\ncast, standardise mcc/ccy"]
  F --> G{"DQ rules\nfuture-date, amount bounds, account exists, ccy has FX"}
  G -->|pass / fixed| H["STAGING.stg_card_txn"]
  G -->|reject| Q[["STAGING.card_txn_QUARANTINE\n+ reason_code"]]
  H --> R{"Reconciliation\nparsed SUM by ccy == file TOTAL\nlanded == staged\ndrift vs 20d mean"}
  R -->|PASS| I["dbt: FACT_CARD_TXN\njoin DIM_ACCOUNT, amount_eur via DIM_FX_RATE"]
  R -->|FAIL| X
  I --> J[("CURATED.FACT_CARD_TXN")]
```

## Core banking & customer master - incremental (watermark)

```mermaid
flowchart TD
  A[("Oracle / SQL Server replica")] -->|"WHERE LAST_MOD_TS / ModifiedUtc > :watermark"| B["Extractor\n(customer_master: FPE tokenise name/DOB/nat-id/address first)"]
  B --> C[["S3 landing (Parquet + manifest)"]]
  B -. real PII .-> P["Restricted load\nCURATED_SENSITIVE"]
  C --> D["RAW -> STAGING cleanse\nstatus/ccy normalise, drop ZZZ test accts"]
  D --> E{"DQ rules"}
  E -->|pass| F["dbt: SCD2 merge\nDIM_ACCOUNT / DIM_CUSTOMER\nvalid_from/to, is_current"]
  E -->|reject| Q[["*_QUARANTINE"]]
  F --> G{"Reconciliation\nsource count == landed == staged\nSCD2 row-count sanity"}
  G -->|PASS| H[("CURATED.DIM_ACCOUNT / DIM_CUSTOMER")]
  G -->|FAIL| X["Halt + PagerDuty"]
  H -. watermark advances only here .-> W[("CURATED.PIPELINE_STATE")]
```

## GL balances - daily snapshot

```mermaid
flowchart TD
  A[("BigQuery gl_replica\ngl_balance_daily, gl_journal_header, chart_of_accounts")] -->|"full snapshot for business_date"| B["Extractor"]
  B --> C[["S3 landing"]]
  C --> D["RAW -> STAGING\nsigned amount_eur, join chart_of_accounts"]
  D --> E{"DQ: debits==credits per journal (zero tolerance)"}
  E -->|pass| F{"Reconciliation\nopening + movements == closing per account/day\nsub-ledger tie-out (WARN only)"}
  E -->|fail| X["Fail run - blocks publish"]
  F -->|PASS| G[("CURATED.FACT_GL_BALANCE")]
  F -->|FAIL| X
```

## FX rates - reference (carry-forward)

```mermaid
flowchart TD
  A(["ECB REST /eurofxref/daily"]) --> B["Extractor 16:30 + retry 20:00"]
  B --> C{"Published for the date?"}
  C -->|yes| D["landing -> RAW -> DIM_FX_RATE merge"]
  C -->|"no (holiday)"| E["carry forward last rate\nis_carried_forward = TRUE"]
  E --> F{"> 4 consecutive carried days?"}
  F -->|yes| X["DQ error - blocks conversions"]
  F -->|no| D
  D --> G[("CURATED.DIM_FX_RATE")]
```

## Zone contract

| Zone | Contents | Mutability | Retention |
|------|----------|-----------|-----------|
| S3 landing / `RAW` | exact source rows as landed (Parquet) | immutable; new `run_id` per replay | 90 days |
| `STAGING` + `*_QUARANTINE` | cleansed rows; rejects + reason codes | replaced per run | 30 days |
| `CURATED` | consumer-facing dimensional model | per load pattern (`02`) | 7 years |
| `CURATED_SENSITIVE` | real PII keyed by `customer_sk` | SCD2 like `DIM_CUSTOMER` | 7 years, crypto-shred on erasure |

## Checkpoints

- **Schema-drift:** after landing, before RAW load - policy: **fail** for
  regulated feeds, **warn** for reference data.
- **DQ:** at STAGING - routes rows pass / fix / quarantine / reject (`04`).
- **Reconciliation:** after STAGING, before the `CURATED` swap - **hard gate** (`05`).
