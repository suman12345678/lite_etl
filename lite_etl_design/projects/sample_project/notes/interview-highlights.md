# Interview highlights - 2026-09-03

> Captured by the `gather-etl-requirements` skill during `/gather-requirements`.
> Shows *how* the interview ran: what was lifted from the intake doc, what was
> asked as a multiple-choice `AskUserQuestion`, what was open prose, and where
> the client said "use your judgement". Fictional.

## Lifted straight from `intake/meridian-trust-rfp-extract.md` (not re-asked)

- 5 sources and their systems; Snowflake as target; EUR reporting currency;
  07:00 CET regulatory extract; SOX / BCBS 239 / GDPR; full PAN must never be
  stored; team knows Python/SQL/dbt/Airflow; < EUR 8k/month; dev/UAT/prod
  separation; real-time out of scope.
- The 4 stated pain points → seeded the reconciliation, lineage, and idempotency
  requirements without asking.

## Asked as `AskUserQuestion` (decisions, small option sets)

| Question | Options offered | Answer |
|----------|-----------------|--------|
| Core banking extract mode? | full / **incremental** / CDC / file-arrival | incremental (`LAST_MOD_TS` confirmed) |
| Card file: how to treat the trailing `TOTAL` line? | drop it / **drop + use as reconciliation control total** / keep as a row | drop + use as control total |
| Load pattern for `DIM_ACCOUNT` / `DIM_CUSTOMER`? | append / upsert / **SCD type 2** / truncate-reload | SCD2 |
| Load pattern for `FACT_CARD_TXN`? | **append (insert), dedup on load** / upsert / SCD2 | append + dedup |
| Where do transforms run? | all ETL (engine) / all ELT (warehouse) / **split** | split (ETL for PII/parse, ELT/dbt for model) |
| Reconciliation failure behaviour? | alert only / **block publish** / block + auto-retry | block publish, no auto-retry |
| Orchestrator? | **Airflow/MWAA** / Step Functions / Dagster / cron | Airflow on MWAA |
| Lineage granularity? | dataset / table / **column-level for regulated fields** | column-level for regulated + GL fields |
| Does dev use real source data? | yes, real replica / **no, synthetic subset** / undecided | undecided → recorded as Q5, assumed synthetic |

## Open prose questions (needed the client's words)

- Business goal & success criteria → `00-project-brief.md` (close 9d→4d, zero
  re-filed submissions, GL tie-out clean 3 month-ends).
- Card file quirks → fixed-width right-justified minor units, Windows-1252, split
  files, trailing summary line (`01-source-systems.md`).
- PII treatment detail → tokenise name/DOB/national-id/address before landing;
  real values only in `CURATED_SENSITIVE`; erasure by crypto-shred
  (`08-security-and-compliance.md`).
- GL tie-out expectations → documented reconciling items expected until manual
  journals removed → tie-out is **warn-only** initially (`05`, ADR-003).

## "Use your judgement" calls (recorded as explicit assumptions)

- Landing format → **Parquet + Snappy** (assumption, `02`).
- Surrogate keys → **`sha256(business_key)`**, no central sequence (`03`).
- Retention split → landing 90d / staging 30d / curated + audit 7y (`08`, `09`).
- FX missing-day handling → **carry forward last rate, max 4 days then DQ error**
  (`03`).
- Backfill approach → one `business_date` per run, oldest first, weekend for the
  13-month go-live seed (`02`, pipeline blueprint).

## Open questions raised → `99-open-questions.md`

Q1 BCBS 239 mandatory field list · Q2 auto-publish vs human sign-off · Q3
intraday card files on the roadmap · Q4 DPO sign-off on erasure test · Q5
dev data source.

## After the interview

- Client answered **Q2** (auto-publish on recon PASS) and **Q4** (DPO approved
  crypto-shred) the same day.
- Ran `/finalize-requirements` → `00`, `07`, `08`, `99` refreshed to v1.1.
- Ran `/design-architecture` → the 9 files in `../design/`.
