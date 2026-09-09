# Design decisions (ADR log) - Meridian Trust (DEMO)

> Produced by `/design-architecture` on 2026-09-03.

## ADR-001: Split ETL (Python) / ELT (dbt) rather than all-in-warehouse ELT

- **Status:** accepted
- **Context:** `08` - full PAN must never persist, PII must be tokenised before
  it reaches Snowflake. `03`/`01` - the card file is Windows-1252, fixed-width,
  with a trailer line. `00`/`09` - team is strong in dbt+SQL.
- **Options:** (1) land raw then do everything in Snowflake - simplest, but full
  PAN and clear PII would transit Snowflake, failing `08`. (2) All-Python ETL -
  meets `08` but throws away the team's dbt skill and set-based strength.
  (3) Split: Python for parse/PII/structure, dbt for model/DQ/recon SQL.
- **Decision:** option 3.
- **Consequences:** two runtimes to operate; a clean security boundary at the
  landing edge; dbt owns the model and most tests. Tokenisation becomes a
  first-class component with its own failure handling.
- **Revisit if:** sources stop containing PAN/PII, or a single-runtime tool
  covers both needs.

## ADR-002: Immutable S3 landing + `run_id` folders, delete-before-insert on reload

- **Status:** accepted
- **Context:** `00` "re-run produces identical output, no double counting"; `02`
  idempotency; `01` known pain point #4 (re-runs double-count today).
- **Options:** (1) overwrite in place - loses history, unsafe mid-run. (2) MERGE
  everything - complex for append facts, hard to reason about for backfill.
  (3) new `run_id` per `(source, business_date)`, facts delete the date's rows
  before insert, dims re-derive SCD2 from the latest snapshot.
- **Decision:** option 3.
- **Consequences:** trivially safe re-runs and backfills; landing storage grows
  (mitigated by 90-day purge); publisher must do the pre-delete inside the
  publish transaction.
- **Revisit if:** landing storage cost becomes material despite lifecycle rules.

## ADR-003: Reconciliation is a hard, non-retrying publish gate

- **Status:** accepted
- **Context:** `05`; `00`/`01` - re-filed submissions caused by reconciliation
  breaks are the problem being solved.
- **Options:** (1) reconcile after publish, alert only - fastest, but bad data
  can reach the regulator. (2) reconcile before publish, auto-retry on FAIL -
  hides systematic breaks. (3) reconcile before publish, **no auto-retry**, FAIL
  blocks the `CURATED` swap and needs a human decision.
- **Decision:** option 3. Sub-ledger↔GL tie-out is **warn-only** at first because
  documented reconciling items are expected until manual journals are removed.
- **Consequences:** a FAIL can delay the 07:00 extract; a documented manual
  fallback exists for a single missed day (`09` RTO). Forces source issues to be
  fixed, not papered over.
- **Revisit if:** tie-out is clean for 3 month-ends → promote it to a hard check.

## ADR-004: Airflow on MWAA for orchestration

- **Status:** accepted
- **Context:** `07` names Airflow; `00`/`09` - 2 engineers know it, managed
  services preferred, prod AWS account locked down.
- **Options:** Step Functions (managed, but the team doesn't know it and DAG
  ergonomics are weaker); self-hosted Airflow (more control, more ops burden,
  against the managed preference); MWAA.
- **Decision:** MWAA, one environment per AWS account.
- **Consequences:** smallest viable environment class for cost (`09`); some MWAA
  version/provider constraints to track; ExternalTaskSensor pattern for the
  gated `curated_build`.
- **Revisit if:** MWAA cost or version lag becomes a blocker.

## ADR-005: Segregate real PII into `CURATED_SENSITIVE` with row-access policy

- **Status:** accepted
- **Context:** `08` GDPR; `06` only named analysts may read real PII; erasure
  via crypto-shred (`99` Q4 resolved).
- **Options:** (1) mask columns in `CURATED` with masking policies only - real
  values still stored in the main schema. (2) separate schema + row-access
  policy + masking, real values only there.
- **Decision:** option 2. `DIM_CUSTOMER` carries tokens; `CUSTOMER_SENSITIVE`
  (1:1 on `customer_sk`) carries real values behind the policy.
- **Consequences:** an extra restricted load path; erasure = crypto-shred key +
  delete the sensitive row, aggregates keep only `customer_sk`.
- **Revisit if:** Snowflake native tag-based governance covers the requirement
  without a second schema.

## Open decisions carried into build

| # | Decision | Options | Blocking? | Linked Q# |
|---|----------|---------|-----------|-----------|
| OD-1 | Exact non-null / `not_null` test set for `CURATED` | draft list now vs final BCBS 239 list | not blocking design; blocks go-live sign-off | Q1 |
| OD-2 | FPE tokenisation vendor / library | Vault Transform FPE vs a dedicated tokenisation service | no - interface is fixed, impl swappable | (new) |
| OD-3 | dev on synthetic subset vs real replica | infra + masking effort differs | no - affects dev test plan only | Q5 |
