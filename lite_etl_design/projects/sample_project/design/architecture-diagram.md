# Architecture diagram - Meridian Trust (DEMO)

> Produced by `/design-architecture` on 2026-09-03. Mermaid renders on GitHub and
> in Claude artifacts; paste into mermaid.live to edit visually.

## System context

```mermaid
flowchart LR
  subgraph SRC["Sources"]
    S1[("Oracle core banking\naccounts + balances")]
    S2[/"Card processor\ndaily PSV over SFTP"/]
    S3[("BigQuery\nGL balance replica")]
    S4(["ECB FX rates\nREST"])
    S5[("SQL Server CRM\ncustomer master - PII")]
  end

  subgraph ETL["Extract + land (Python on MWAA workers)"]
    EX["Extractors x5\nincr / file-arrival / snapshot"]
    PAR["Card parser\ndecode, strip TOTAL, drop full PAN -> last4"]
    TOK["PII tokeniser (FPE)\nname/DOB/nat-id/address"]
    LW["Landing writer\nParquet + manifest.json + _SUCCESS"]
  end

  L[["S3 landing\n<domain>/<source>/business_date=/run_id=/"]]

  subgraph SF["Snowflake RISK_DWH"]
    RAW[["RAW\ncopy of landing"]]
    STG[["STAGING\ncleanse, cast, quarantine"]]
    DQ{"DQ engine\nrules + thresholds"}
    Qz[["*_QUARANTINE\n+ reason codes"]]
    REC{"Reconciliation gate\nrow counts, control totals, GL balance"}
    CUR[["CURATED\nDIM_* / FACT_*"]]
    CURS[["CURATED_SENSITIVE\nreal PII, row-access policy"]]
  end

  RE["Regulatory extract\n07:00 CET (existing engine)"]
  FIN["Finance month-end close"]

  subgraph CTRL["Orchestration & governance"]
    AF["Airflow / MWAA\nper-source DAGs + curated_build"]
    DH[("DataHub\nOpenLineage + catalog")]
    OBS["CloudWatch + health dashboard\nPagerDuty / Slack"]
    SEC["Secrets Manager + Vault\nKMS keys"]
  end

  S1 --> EX
  S2 --> PAR --> EX
  S3 --> EX
  S4 --> EX
  S5 --> TOK --> EX
  EX --> LW --> L --> RAW --> STG --> DQ
  DQ -->|pass / fixed| REC
  DQ -->|reject| Qz
  REC -->|PASS| CUR
  REC -->|FAIL| OBS
  TOK -. real values via restricted path .-> CURS
  CUR --> RE
  CUR --> FIN

  AF -. triggers .-> EX
  AF -. triggers .-> STG
  AF -. triggers .-> REC
  LW -. manifest .-> DH
  STG -. OpenLineage .-> DH
  CUR -. OpenLineage .-> DH
  SF -. metrics/logs .-> OBS
  SEC -. resolves refs .-> ETL
  SEC -. row-access + KMS .-> SF
```

## Notes

- **Zones:** `S3 landing`/`RAW` = exact source content (Parquet); `STAGING` =
  cleansed + quarantined; `CURATED` = consumer-facing model; `CURATED_SENSITIVE`
  = real PII only, separate restricted load path.
- **The reconciliation gate is hard** (`05`): FAIL ⇒ no `CURATED` swap, no
  `_SUCCESS`, business date stays open, PagerDuty Sev2.
- **Full PAN** exists only in memory inside the card parser; it is never written
  to landing, RAW, or anywhere else (`08`).
