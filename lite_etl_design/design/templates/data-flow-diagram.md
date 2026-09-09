# Data-flow diagram

> How data moves through the zones, per source. One diagram per source (or a
> combined one if they are similar). Show batch vs stream and where the DQ and
> reconciliation checkpoints sit.

## Source: `<slug>` - `<mode>` (`full` / `incremental` / `cdc` / `file-arrival`)

```mermaid
flowchart TD
  A[(Source: &lt;system&gt;)] -->|"extract query / file glob\nwatermark = updated_at"| B[Raw landing\n&lt;domain&gt;/&lt;source&gt;/&lt;load_date&gt;/&lt;run_id&gt;/data.parquet]
  B -->|"schema check vs contract"| C{Schema drift?}
  C -->|no| D[Transform\ntrim, cast, map codes, dedupe]
  C -->|yes| X[Halt + alert]
  D --> E{DQ rules}
  E -->|pass / fixed| F[Curated staging\nstg_&lt;entity&gt;]
  E -->|reject| Q[Quarantine\nrejects.parquet + reason_code]
  F --> G{Reconciliation\nrow counts + control totals}
  G -->|PASS| H[Load to target\n&lt;pattern: upsert / SCD2&gt;]
  G -->|FAIL| X
  H --> I[(Target: &lt;table&gt;)]
  H -->|advance watermark| J[(State store)]
```

## Zone contract

| Zone | Contents | Mutability | Retention |
|------|----------|-----------|-----------|
| Raw landing | exact source rows, as landed | immutable, new run_id per replay | from 02 |
| Quarantine | rejected rows + reason codes | append | from 04 |
| Curated staging | transformed, DQ-passed, pre-publish | replaced per run | short |
| Target | consumer-facing model | per load pattern | from 02 |

## Checkpoints

- **Schema drift check:** after landing, before transform - policy: fail / warn / evolve
- **DQ checkpoint:** during/after transform - routes rows pass / fix / quarantine / reject
- **Reconciliation checkpoint:** after staging, before load - hard gate
