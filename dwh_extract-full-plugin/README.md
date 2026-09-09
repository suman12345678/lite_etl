# dwh_extract-full-plugin

An **enterprise data-warehouse extraction plugin** for Claude Code — structure
first. It defines the full shape of a production extraction stage:

```
requirements ─▶ config ─▶ EXTRACT ─▶ BUSINESS RULES ─▶ LANDING ZONE ─▶ RECONCILE ─▶ publish/notify
 (what to pull)          (any source)  (standard DQ +    (atomic,        (prove it,
                                        custom checks)    partitioned)    then gate)
```

Everything is **generic** and **config-driven**: you add a source by dropping a
requirements file (or editing YAML), not by writing code. New source *types*,
rules, checks, and landing targets plug into registries.

> **Status: SCAFFOLD.** This repo currently contains the folder/file structure
> and placeholders only. No extraction logic is implemented yet. Fill components
> in one at a time; the layout and contracts below are meant to stay stable.

---

## 1. Where you put things & how you run it

### You provide requirements here
`dwh-extract-full/requirements/inbox/` — drop a filled-in template (or any spec
doc: Word, Excel, PDF, CSV data dictionary, email). See
`dwh-extract-full/requirements/README.md` for the full flow. Short version:

1. Put your file in `requirements/inbox/`.
2. `/ingest-requirements` (or ask the `requirements-analyst` agent) → it drafts
   `config/sources/…`, `config/business_rules/…`, `config/reconciliation/…`,
   `config/data_contracts/…` and lists what it couldn't infer.
3. Review/edit the drafts. `/validate-config`.
4. `/extract <source>` → `/dq-report <source>` → `/reconcile <source>`.
5. Move the intake file to `requirements/processed/`.

### Or configure a source directly
Copy `config/sources/_template.source.yaml` → `config/sources/<name>.source.yaml`
and fill it. Same for a ruleset, recon spec, and (optionally) a data contract.

### Landing zone
Default local root: `dwh-extract-full/landing_zone/`. Change it in
`config/landing_zone/layout.yaml` or via `ETL_LANDING_ROOT`. Later, point it at
S3 / GCS / Azure Blob via `landing/targets/`. Layout:

```
<landing_root>/<domain>/<source>/<load_date=YYYY-MM-DD>/<run_id>/
    data.<fmt>            landed dataset (parquet by default)
    rejects.<fmt>         rows that failed business rules (+ reason codes)
    manifest.json         counts, control totals, schema, checksums, rules applied, lineage
    _reconciliation.json  every check, expected vs actual, overall PASS/FAIL
    _SUCCESS             written only after a clean, reconciled commit
```

### Install (local)
```
/plugin marketplace add C:\Users\sahaa\suman_on_computer\claude\dwh_extract-full-plugin
/plugin install dwh-extract-full@dwh-extract-full-marketplace
```
Needs Python 3.9+ on `PATH`. Base engine targets the standard library; connector
dependencies get added to `dwh-extract-full/scripts/requirements.txt` as you build them.

---

## 2. Directory map

```
dwh_extract-full-plugin/
├── .claude-plugin/marketplace.json          local marketplace
├── README.md                                this file
├── CHANGELOG.md
└── dwh-extract-full/                         the plugin
    ├── .claude-plugin/plugin.json
    ├── .mcp.json                             MCP server registration
    │
    ├── commands/                             /slash commands (thin CLI wrappers)
    │   extract · extract-all · reconcile · validate-config · dq-report
    │   landing-status · quarantine-review · backfill · register-source · ingest-requirements
    ├── agents/                               task agents
    │   requirements-analyst · source-onboarder · business-rules-author
    │   reconciliation-analyst · extraction-reviewer · incident-responder
    ├── skills/                               how-to skills
    │   run-extraction · onboard-data-source · author-business-rules
    │   configure-landing-zone · define-reconciliation · interpret-requirements · operate-and-monitor
    ├── hooks/hooks.json                      SessionStart orientation hook
    │
    ├── requirements/                         ◀── YOU UPLOAD HERE
    │   inbox/  templates/  examples/  processed/  README.md
    │
    ├── config/                               ◀── the whole pipeline is defined here
    │   settings.yaml                         active env, landing root, parallelism, state backend
    │   connections/     *.connection.yaml    reusable connection profiles (secret *refs*, no values)
    │   sources/         *.source.yaml        per-source: connection + object + mode + rule/recon/contract refs
    │   business_rules/  *.ruleset.yaml       ordered rule invocations; _standard_rules.yaml = catalog
    │   reconciliation/  *.recon.yaml         checks, tolerances, baselines, on-fail action
    │   data_contracts/  *.contract.yaml      expected schema, semantic types, constraints, SLAs, owner
    │   landing_zone/    layout.yaml retention.yaml
    │   masking/         policies.yaml        classification → masking action
    │   schedules/       *.schedule.yaml      cron, SLA, deps, catch-up
    │   environments/    dev.yaml test.yaml prod.yaml   overlays
    │   secrets/README.md                     how secret references resolve
    │
    ├── scripts/
    │   etl_cli.py                            CLI entry point
    │   mcp_server.py                         stdio MCP server
    │   requirements.txt
    │   hooks/session_context.py
    │   dwh_extract/                          the engine (Python package)
    │       config/        loader · schema · resolver
    │       connectors/    base · filesystem · rdbms · (bigquery/snowflake/s3/azure_blob/gcs/sftp/rest_api/kafka .example)
    │       formats/       csv · json · parquet · (avro/fixed_width .example)
    │       extract/       planner · watermark · partitioner · runner · schema_drift
    │       business_rules/ engine · standard/{completeness,uniqueness,validity,consistency,
    │                       referential,timeliness,conformity,accuracy,standardization,pii} · custom/
    │       landing/       writer · layout · retention · catalog · targets/{local_fs, s3/gcs/azure_blob .example}
    │       reconciliation/ engine · report · checks/{row_counts,control_totals,column_hash,
    │                       financial_balance,referential,completeness,duplicates,drift}
    │       quarantine/    store · reprocess
    │       state/         run_store · backend/{sqlite,jsonl}
    │       observability/ logging · metrics · lineage · alerts
    │       security/      secrets · classification · masking
    │       orchestration/ pipeline · retry · idempotency · adapters/{airflow,dagster,prefect .example, cron.md}
    │       requirements_intake/ parser · mapper · validator
    │       utils/         hashing · time · io
    │
    ├── landing_zone/                         default local landing root (gitignored contents)
    ├── reference_data/                       lookup datasets for referential checks
    ├── state/                                run registry / watermarks (gitignored)
    ├── logs/                                 (gitignored)
    ├── tests/                                unit · integration · contract · data_quality · fixtures
    └── docs/                                 architecture · extraction-patterns · business-rules-catalog
                                             landing-zone-spec · reconciliation-spec · requirements-intake
                                             security-and-compliance · observability · operations-runbook
                                             testing-strategy · extending
```

---

## 3. Config model (how the pieces relate)

| File | Answers | Reused by |
|------|---------|-----------|
| `connections/*.connection.yaml` | *How do we reach a system?* endpoint + auth method + secret refs | many sources |
| `sources/*.source.yaml` | *What do we pull, how often, in what mode?* → points at a connection, a ruleset, a recon spec, a contract, a landing target, a schedule | one source |
| `business_rules/*.ruleset.yaml` | *What checks/transforms run during extraction?* ordered list from the standard catalog + custom | one or more sources |
| `reconciliation/*.recon.yaml` | *How do we prove the run is correct before publishing?* | one or more sources |
| `data_contracts/*.contract.yaml` | *What schema/semantics do we expect?* drives schema-drift detection | one source |
| `masking/policies.yaml` | *classification → mask/hash/tokenize/redact* | PII rules, everywhere |
| `schedules/*.schedule.yaml` | *cron, SLA, dependencies, catch-up* | orchestration |
| `environments/{dev,test,prod}.yaml` | *per-env overrides* (endpoints, paths, strictness, alerting) | everything |

---

## 4. Extraction — full scope

**Modes** (`extract/planner.py`): `full` · `incremental` (watermark column, stored
in `state/`) · `cdc` (log/trigger-based deltas) · `file-arrival` (process new files
in a drop) · bounded `streaming` (Kafka pull to a checkpoint).

**Also covered by the structure:**
- Parallel extraction via `partitioner.py` (date windows / key ranges / file lists), restartable per partition.
- Schema-drift detection vs the data contract (`schema_drift.py`): fail / warn / auto-evolve policy.
- Watermark advance only on a fully reconciled run; rollback on failure.
- Idempotency keys + run registry (`state/run_store.py`) so a re-run never double-lands.
- Retry/resume policy for transient vs permanent errors (`orchestration/retry.py`).
- Per-source connection pooling, rate limiting, pagination (connector concern).

---

## 5. Standard business-rule checks (applied during extraction)

`business_rules/engine.py` runs a ruleset over each batch and routes every row to
**pass / fix-in-place / quarantine / reject**, recording per-rule metrics.
Standard library (`business_rules/standard/`), by DQ dimension:

| Dimension | Examples |
|-----------|----------|
| **Completeness** | required columns present, not-null, min fill-rate, mandatory-when-condition |
| **Uniqueness** | primary/business key unique, exact & fuzzy dedupe, dedupe strategy |
| **Validity** | data type, numeric/date range, string length, regex/pattern, enum / allowed values, check digits |
| **Consistency** | cross-field logic, cross-row, cross-dataset, aggregate tie-outs |
| **Referential** | value exists in reference data or a prior load |
| **Timeliness** | freshness window, no future dates (+skew), effective-dating, late-arrival handling |
| **Conformity** | trim, case, whitespace collapse, unicode/encoding normalization, date/number formats |
| **Accuracy** | control digits (IBAN/ISIN/LUHN), geo/postal sanity, tolerance vs source of truth |
| **Standardization** | rename, cast, derive, code-mapping, currency / unit-of-measure normalization |
| **PII** | detect + classify, then mask / hash / tokenize / redact per `masking/policies.yaml` |

**Custom rules**: add a function in `business_rules/custom/` following the rule
contract; reference it by name in any ruleset. Each rule declares a **severity**
(info/warn/error) and an **on-fail action**.

---

## 6. Landing zone loading — full scope

`landing/writer.py` + `landing/layout.py`:
- **Atomic commit**: write to a staging path, then move/rename; readers never see a partial dataset.
- **Markers & metadata**: `_SUCCESS`, `manifest.json` (row counts, control totals, schema snapshot, file checksums, rules applied, source→landing lineage), `_reconciliation.json`.
- **Partitioning & versioning**: `<domain>/<source>/<load_date>/<run_id>/`; late data and replays get new `run_id`s, never overwrite.
- **Formats**: parquet default; csv/json/avro/fixed-width supported.
- **Targets** (`landing/targets/`): local filesystem now; S3 / GCS / Azure Blob templates — same layout, just a different byte sink.
- **Retention** (`landing/retention.py`): per-domain keep/archive/purge.
- **Catalog registration** (`landing/catalog.py`): register the new partition in Glue / BigQuery / Unity / Hive / a file catalog so the warehouse load can pick it up.
- **Quarantine / dead-letter** (`quarantine/`): rejected rows land with reason codes; `reprocess.py` replays them after a fix.

---

## 7. Reconciliation — full scope

`reconciliation/engine.py` gathers metrics from **source**, **landing**, and
**rejects**, evaluates the spec, and `report.py` emits `_reconciliation.json` with
an overall **PASS/FAIL**. A hard FAIL blocks `_SUCCESS`/publish and makes the CLI
exit non-zero (gate the warehouse load on it).

| Check | Proves |
|-------|--------|
| `row_counts` | `source == landed + rejected + filtered`, per partition |
| `control_totals` | SUM/AVG/MIN/MAX of measures conserved source → landing |
| `column_hash` | row-fingerprint / set-hash match source vs landing |
| `financial_balance` | debits == credits, opening + Δ == closing, GL tie-out |
| `referential` | landed keys covered by reference data |
| `completeness` | no dropped/added records; mandatory partitions present |
| `duplicates` | no unexpected duplicates in landed data |
| `drift` | volume / null-rate / distribution within tolerance of a historical baseline |

Each check has a **tolerance** and an **on-fail action** (fail run / warn / alert).

---

## 8. Cross-cutting

- **Security** (`security/`): secret references only (`env://`, `file://`, `vault://`, `awssm://`, `gcpsm://`, `azkv://`) resolved at run time; data classification tags; masking/tokenization/FPE. See `config/secrets/README.md` and `docs/security-and-compliance.md`.
- **Observability** (`observability/`): structured JSON logs, metrics (rows/bytes/duration/reject-rate/freshness lag), OpenLineage-style lineage events, alert routing (SLA breach, recon FAIL, drift, schema change).
- **Orchestration** (`orchestration/`): run via CLI, MCP tools, or an external scheduler (`adapters/` for Airflow / Dagster / Prefect / cron). One pipeline: plan → extract → rules → land → catalog → reconcile → publish/notify.
- **Environments**: `config/environments/{dev,test,prod}.yaml` overlays merged over `settings.yaml`.
- **Backfill / replay**: `/backfill <source> --from --to` re-extracts a window idempotently.

---

## 9. Testing

`tests/` (pytest), to be filled alongside each feature:

| Suite | Covers |
|-------|--------|
| `unit/` | config loader, each business rule, each recon check, landing writer, watermark |
| `integration/` | filesystem connector, full local pipeline → landing → reconcile PASS |
| `contract/` | sample data conforms to its data contract; drift is detected |
| `data_quality/` | standard-rule behaviour matrix on crafted inputs |
| `fixtures/` | sample sources + expected reconciliation outputs |

CI: run `validate-config` + `pytest` on every change; block merge on failure.

---

## 10. Plugin surface

| Type | Items |
|------|-------|
| **Commands** | `/extract` `/extract-all` `/reconcile` `/validate-config` `/dq-report` `/landing-status` `/quarantine-review` `/backfill` `/register-source` `/ingest-requirements` |
| **Agents** | `requirements-analyst` `source-onboarder` `business-rules-author` `reconciliation-analyst` `extraction-reviewer` `incident-responder` |
| **Skills** | `run-extraction` `onboard-data-source` `author-business-rules` `configure-landing-zone` `define-reconciliation` `interpret-requirements` `operate-and-monitor` |
| **Hook** | `SessionStart` → `scripts/hooks/session_context.py` (orientation + pending inbox files) |
| **MCP** | `dwh-extract-full` stdio server (`scripts/mcp_server.py`) — advertises 0 tools today; will expose extract/reconcile/dq-report/landing-status/ingest-requirements |

---

## 11. Build order (suggested, to add incrementally)

1. `config/` loader + schema + resolver, and `settings.yaml` / templates.
2. `connectors/base.py` + `connectors/filesystem.py` + `formats/csv.py`.
3. `extract/runner.py` (full mode only) + `landing/writer.py` + `landing/targets/local_fs.py`.
4. `business_rules/engine.py` + 3–4 standard rules (completeness, uniqueness, validity, conformity).
5. `reconciliation/engine.py` + `row_counts` + `control_totals` + `report.py`.
6. Wire `etl_cli.py` `extract` / `reconcile` / `validate-config` for real; first green `tests/integration/test_end_to_end_local.py`.
7. `state/` watermark + `extract/planner.py` incremental mode.
8. `requirements_intake/` + `/ingest-requirements` + `requirements-analyst` agent.
9. `quarantine/`, `observability/`, `security/secrets.py`.
10. Cloud connectors + cloud landing targets + `orchestration/adapters/`.

Update `CHANGELOG.md` as each lands.
