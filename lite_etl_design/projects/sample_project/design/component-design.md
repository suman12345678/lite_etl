# Component design - Meridian Trust (DEMO)

> Produced by `/design-architecture` on 2026-09-03. Condensed to the components
> that carry risk for this project.

### Source extractor (generic + 5 connector impls)

- **Responsibility:** pull one source object for one `business_date` into S3
  landing as Parquet, with a `manifest.json`. Nothing else - no business logic.
- **Triggered by:** the source's Airflow DAG (schedule or S3 sensor).
- **Inputs:** connection ref (`awssm://` / `vault://`), object spec, watermark
  (from `CURATED.PIPELINE_STATE`), `business_date`.
- **Outputs:** `s3://.../<source>/business_date=/run_id=/data-*.parquet`,
  `manifest.json` (rows, checksums, min/max watermark, code version), OpenLineage
  start/complete events.
- **Config:** batch size, fetch parallelism, per-source rate limit; per-env
  endpoints in `environments/<env>.yaml`.
- **Key logic:** resolve secret → open connection → page result / read file(s) →
  write Parquet parts → write manifest → emit lineage.
- **Failure modes:**

  | Failure | Detection | Response |
  |---------|-----------|----------|
  | connection / throttle | exception | retry 3× expo, then fail task |
  | source unavailable at SLA | sensor timeout 03:30 | fail, PagerDuty, date stays open |
  | zero rows when rows expected | manifest vs drift baseline | warn (some days are legitimately empty) |

- **Idempotency:** re-run writes a new `run_id`; landing is append-only per date.
- **Scaling knobs:** fetch parallelism, Parquet part size.

### Card file parser (inside the card extractor)

- **Responsibility:** turn 1-2 `.psv` parts into clean typed rows; produce the
  control totals; **ensure full PAN never leaves the process**.
- **Inputs:** raw file parts from S3, expected `business_date`.
- **Outputs:** parsed Parquet, `control_totals.json` (count + sum minor units by
  ccy, from the `TOTAL` trailer and independently recomputed).
- **Key logic:** decode Windows-1252 → validate header → for each line: split on
  `|`, drop the trailing `TOTAL` line (capture it), parse right-justified
  zero-padded amount → `DECIMAL/100`, `POST_DATE` `YYYYMMDD` → date,
  `pan_last4 = pan[-4:]`, **discard `pan`** → yield row.
- **Failure modes:** missing part (both expected) → wait/timeout; header mismatch
  → fail; `TOTAL` mismatch vs recomputed → still land, flag for reconciliation.
- **Idempotency:** pure function of the input files.

### PII tokeniser

- **Responsibility:** FPE-tokenise `full_name`, `date_of_birth`, `national_id`,
  `address_*` before landing; route the real values to the restricted
  `CURATED_SENSITIVE` load path.
- **Inputs:** extracted customer rows, Vault-managed FPE keys.
- **Outputs:** tokenised rows for the normal path; real rows for the restricted
  path (encrypted channel, separate S3 prefix with tighter policy).
- **Failure modes:** Vault unavailable → fail (no fallback to plaintext);
  key version mismatch → fail.
- **Idempotency:** deterministic per key version; token stable across reloads.

### Reconciliation engine

- **Responsibility:** after STAGING, compute the `05` checks, write
  `_reconciliation.json`, and return PASS/FAIL that gates the `CURATED` swap.
- **Inputs:** source manifests, landing metrics, STAGING aggregates, control
  totals, trailing 20-day baselines, the `.recon.yaml` spec for the feed.
- **Outputs:** `_reconciliation.json` (every check, expected vs actual, tolerance,
  status), a row in `CURATED.RECON_DAILY`, PASS/FAIL exit.
- **Key logic:** load spec → run each check → apply tolerance → overall = AND of
  all hard checks → emit report → on FAIL, do not write `_SUCCESS`.
- **Failure modes:** missing input metric → treated as FAIL (never skip a check);
  baseline not yet 20 days → drift check = warn-only.
- **Idempotency:** read-only; safe to re-run.

### Transform + model (dbt)

- **Responsibility:** STAGING cleanse, SCD2 merges, FX conversion, dimensional
  build, set-level DQ tests.
- **Inputs:** `RAW`/`STAGING` tables, reference seeds, `DIM_FX_RATE`.
- **Outputs:** `CURATED.DIM_*` / `FACT_*`, `dbt` run artifacts + OpenLineage.
- **Config:** `dbt` vars for `business_date`, target schema per env.
- **Failure modes:** `not_null` / `unique` / `relationships` test failure → fail
  `curated_build`, no publish; SCD2 ambiguity (two changes same `LAST_MOD_TS`) →
  deterministic tiebreak on source PK.
- **Idempotency:** `--full-refresh` reproduces; incremental models keyed by
  `business_date` re-run cleanly after the pre-delete step.

### Publisher

- **Responsibility:** atomically move a reconciled `business_date` into
  `CURATED`, write `_SUCCESS`, advance the watermark.
- **Key logic:** single transaction — delete/replace the date's rows in the
  target facts, apply SCD2 dim updates, commit; on commit write `_SUCCESS` to S3
  and update `CURATED.PIPELINE_STATE`.
- **Failure modes:** transaction failure → nothing committed, watermark
  unchanged, task fails.
- **Idempotency:** re-publish of the same date replaces, never appends.

### Orchestration (Airflow / MWAA)

- **Responsibility:** schedule the DAGs in `07`, wire dependencies, retries,
  backfill, alert routing.
- **Key logic:** per-source DAG (extract → land → drift → RAW → STAGING → DQ);
  `curated_build` DAG gated by an ExternalTaskSensor on all source DAGs for the
  `business_date`, then dbt → reconcile → publish.
- **Failure modes:** upstream DAG failed/late → `curated_build` does not start,
  SLA miss alert at 06:00.
- **Idempotency:** DAG runs keyed by `logical_date` = `business_date`.

### Lineage & catalog / Secrets / Observability / Pipeline state

- **Lineage:** OpenLineage from extractors + dbt → DataHub; `manifest.json` →
  `CURATED.RUN_MANIFEST`; 7-year retention.
- **Secrets:** resolver for `awssm://` and `vault://…#field`; never logged;
  cached in-process for the run only.
- **Observability:** JSON logs → CloudWatch; metrics (rows, bytes, duration,
  reject rate, freshness lag, credits, recon status) → the health dashboard;
  PagerDuty Sev2 for SLA/recon/DQ-block, Slack for warnings.
- **Pipeline state:** `CURATED.PIPELINE_STATE` (source, business_date, run_id,
  watermark, status); Time Travel + replication for durability.
