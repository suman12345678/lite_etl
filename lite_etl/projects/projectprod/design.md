# Design — projectprod

## Approach
ELT: land raw -> dbt (`<engine>`) -> rule checks -> publish.
Orchestrator: cron — a daily 02:00 run (full transform + publish) plus an hourly
land-only run that appends new invoices to raw. Infra: Terraform.

The bundled local demo (`repo/demo/`) runs the whole flow on **DuckDB / stdlib SQLite** —
no cloud, no credentials. The transform SQL in `demo/sql/` is the same SQL used as the
dbt model bodies, so the local run is faithful to the warehouse run.

## Components
| component | does | spec ref |
|-----------|------|----------|
| extract/billing | pull `billing.invoices` + `billing.subscriptions` (REST, incremental by `updated_at`) -> raw | Sources |
| extract/crm | pull the daily `crm.accounts` Postgres snapshot -> raw | Sources |
| extract/ref | pull `ref.plans` + `ref.fx_rates` CSVs -> raw | Sources |
| dbt · staging | raw -> `stg_*`: snake_case, cast dates, dedupe invoices on latest `updated_at`, resolve merged `account_id`, hash `billing_email`, drop `company_name` (keep `company_domain`) | Target, Transforms |
| dbt · marts | `stg_*` -> `dim_account`, `dim_plan`, `fct_invoice`, `fct_mrr_movement`: FX carry-forward join, `amount_usd`, `recognized_revenue_usd`, prorated MRR, movement classification | Target, Transforms |
| rules | run `rules.yml`: 5 quality checks (warn / quarantine / fail) + 2 reconciliations (revenue vs finance GL; MRR movement identity) — quarantine bad rows, block publish on a recon break | Rules |
| publish | write `gold/` + `_SUCCESS` + advance the `month` watermark; idempotent replace per month; or block and exit 1 | Target, Schedule |
| infra | `engine` (duckdb \| databricks \| snowflake), landing storage, warehouse/catalog, roles — one Terraform module, one `envs/<env>` per env | Non-functional, envs |
| ci | lint · `make demo` · `make demo-fail` · `dbt build --target ci` · `terraform validate` | envs |

## Data flow
see diagram.md

## Decisions
- **ELT with dbt** because every item in Transforms is set-based SQL over landed tables — no
  row-by-row processing needed.
- **Orchestrator = cron, two cadences** because Schedule asks for a daily 02:00 transform+publish
  *and* an hourly run that only lands new invoices (no transform, no publish).
- **Local demo runs on DuckDB / SQLite** because the spec sets `engine: duckdb` for the local demo
  and Non-functional caps demo cost at $0 — `python -m demo.run` needs no cloud.
- **`engine` is a single Terraform variable** (`duckdb | databricks | snowflake`) because the prod
  engine is an Open question and every transform is plain dbt SQL — only the connection profile and
  a couple of macros change.
- **One `rules.yml` for quality *and* reconciliation** because the spec's Rules section keeps them
  together; `demo/rules.py` runs it locally, dbt tests + the publish gate run it in prod.
- **Dedupe invoices on latest `updated_at` in staging** because Sources notes webhook retries
  re-send the same `invoice_id`.
- **Resolve merged accounts in staging, before any aggregation** because Sources notes an old
  `account_id` can point to a surviving id — MRR and revenue would double-count otherwise.
- **FX gaps → carry forward the last known rate** because Sources notes weekend / holiday gaps in
  `ref.fx_rates`.
- **PII hashed at the staging boundary + a marts-wide "no raw email" `fail` rule** because
  Non-functional requires raw `billing_email` / `company_name` never reach staging or marts.
- **Quarantine vs block**: row-level quality problems (`amount_usd < 0`, unknown `status`) divert
  the row to `reject_fct_invoice` and the run continues; a reconciliation break means the published
  totals would be wrong, so it blocks and exits non-zero. Matches the `on_fail` values in Rules.
- **MRR movement identity is a *blocking* reconcile** (`closing = opening + new + expansion −
  contraction − churn + reactivation`, tol 0.1%) because Rules marks it `on_fail: block`.
- **Backfill = idempotent replace per `month`** because Schedule requires re-running a month by
  date range without duplicating rows.
- **This project builds the full production path** (`/etl-build-prod`, on top of `/etl-build`)
  because `projectprod` targets real sources with real credentials — `extract/billing`,
  `extract/crm`, and `extract/ref` above must become real client code (env-var credentials only),
  and `infra` must provision real per-engine resources instead of the `terraform_data` placeholder
  `etl-build` leaves behind.

## Maps to spec
- **Sources**: `billing.invoices` → extract/billing, dbt·staging (dedupe); `billing.subscriptions` →
  extract/billing, dbt·marts (MRR); `crm.accounts` → extract/crm, dbt·staging (merge-resolve, PII);
  `ref.plans` → extract/ref, dbt·marts (`dim_plan`); `ref.fx_rates` → extract/ref, dbt·marts (FX join).
- **Target**: zones raw→staging→marts → dbt·staging + dbt·marts; `dim_account` / `dim_plan` /
  `fct_invoice` / `fct_mrr_movement` + keys → dbt·marts, publish.
- **Transforms**: snake_case/cast → dbt·staging; dedupe invoices → dbt·staging; merged-account
  resolution → dbt·staging; FX carry-forward join + `amount_usd` → dbt·marts; `recognized_revenue_usd`
  → dbt·marts; prorated MRR + movement classification → dbt·marts; email hash / drop company_name →
  dbt·staging.
- **Rules**: 4 quality checks + the plan-code `warn` → rules (+ dbt tests); PII guard → rules,
  dbt·staging; revenue-vs-GL reconcile + MRR-movement reconcile → rules, publish.
- **Schedule**: daily 02:00 + hourly land-only → ci, publish, extract/billing; backfill by month →
  publish.
- **Non-functional**: volume / latency → infra (warehouse sizing), dbt·marts (incremental later);
  cost ceiling → infra; pii → dbt·staging, rules; envs dev/prod → infra, ci.

Gaps: none. The four Open questions in the spec are deferred *decisions* (prod engine, proration
rule, reporting currency, late-invoice restatement), not missing components — each has a named home
(infra `engine` var; dbt·marts MRR proration; dbt·marts output; publish/backfill policy) for when
they are answered.
