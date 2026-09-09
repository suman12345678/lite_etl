# Data-entity diagram (ER)

> Mermaid `erDiagram`. Model the **target** first (dimensions/facts or normalised
> entities), then the key **staging** entities. Entity and attribute names must
> match `02-targets-and-loading.md` and `03-transformations.md`.

## Target model

```mermaid
erDiagram
  DIM_CUSTOMER ||--o{ FCT_ORDER : places
  DIM_PRODUCT  ||--o{ FCT_ORDER : "appears in"
  DIM_DATE     ||--o{ FCT_ORDER : "ordered on"

  DIM_CUSTOMER {
    bigint  customer_sk PK "surrogate, hash(business key)"
    string  customer_id  "natural / business key"
    string  name
    string  country
    date    valid_from   "SCD2"
    date    valid_to     "SCD2"
    boolean is_current    "SCD2"
  }

  FCT_ORDER {
    bigint  order_sk PK
    bigint  customer_sk FK
    bigint  product_sk  FK
    int     date_sk     FK
    decimal amount
    string  currency
    string  source_run_id "lineage"
  }

  DIM_PRODUCT {
    bigint product_sk PK
    string product_id
    string category
  }

  DIM_DATE {
    int  date_sk PK
    date calendar_date
  }
```

## Staging entities

```mermaid
erDiagram
  STG_CUSTOMER {
    string customer_id
    string name_raw
    string name_clean
    string country_raw
    string country_iso
    timestamp updated_at "watermark"
    string _run_id
    string _dq_status "pass / fixed / reject"
  }
```

## Notes

- **Keys:** business key vs surrogate key strategy (from 02/03).
- **Historisation:** which entities are SCD2 and the tracked columns (from 03).
- **Lineage columns:** `_run_id` / `source_run_id` carried into curated per 06.
- **Grain:** state the grain of every fact table explicitly.
