# project2 — runbook (build it, then demo it)

Subscription revenue analytics pipeline. Input brief: `requirements.md`.

- **Part A** — the harness commands that turn the brief into a runnable `repo/`. **Done** —
  `repo/` exists. Kept here as the record of how it was built.
- **Part B** — the two-minute script to run and demo it.

---

# Part A — build it with the harness  *(already run)*

From `lite_etl/` (the harness root). Each phase wrote files into `projects/project2/`.

| # | command | wrote | check |
|---|---------|-------|-------|
| 1 | `/etl-spec project2` | `spec.md`, `progress.json`, `state/active` | every brief section landed; 4 undecided items under **## Open questions** |
| 2 | `/etl-design` | `design.md`, `diagram.md` | "Maps to spec" → *Gaps: none*; mermaid renders |
| 3 | `/etl-build` | `repo/` — `demo/` (+ `peek.py`), `dbt/`, `rules.yml`, `infra/`, `.github/`, `Makefile`, `README.md` | smoke test below |
| — | `/etl-status` | — | prints phase + next command anytime |

### Smoke test (already passing)

```
cd projects/project2/repo
python -m venv .venv && .venv\Scripts\activate       # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m demo.run                 # -> exit 0, publishes 4 gold tables
python -m demo.run --scenario fail # -> exit 1, publish blocked
```

---

# Part B — run & demo it

All commands from `projects/project2/repo` with the venv active.

## 0. Show what the harness worked from (10 sec)
Open `../spec.md` (the formalised brief) and `../design.md` ("Maps to spec" — every component
names the spec line it satisfies). "Here's what it scaffolded from those two files."

## 1. Look at the inputs — BEFORE the run (20 sec)

```
python -m demo.peek inputs
```

Three things it prints:

| shown | file | point to make |
|-------|------|---------------|
| source recipe | `demo/load.py` | deterministic synthetic `invoices` / `subscriptions` / `accounts` / `plans` / `fx_rates`; planted quirks — a **webhook retry** (deduped), a **merged account** (`A013 → A007`), a **weekend/holiday FX gap** (GBP missing for the current month → carry forward), and in `--scenario fail` an **unknown plan code** |
| finance control total | `demo/data/control_totals.csv` | one line, **editable on stage** — `recognized_revenue_usd_current_month,1500.00` |
| the rules | `rules.yml` | 5 quality checks + 2 reconciliations in one file; `on_fail: warn / quarantine / fail / block` |

## 2. Clean run — the happy path (30 sec)

```
python -m demo.run           # or: make demo
```

Stages it prints: **LOAD** (`raw.*`) → **TRANSFORM** (note *"deduped 1 webhook invoice; resolved
1 merged account"*) → **RULES GATE** (all 5 quality checks `ok`; `revenue_vs_finance_gl` 1,500 ==
1,500; `mrr_movement_identity` 1,500 == 1,500) → **VERDICT** (`published gold/` — `dim_account`,
`dim_plan`, `fct_invoice`, `fct_mrr_movement` — + `_SUCCESS`, watermark `month <= 2026-07`).

### Check the outputs — AFTER the run

```
python -m demo.peek
```

- **Row counts** — `raw_* → stg_* → dim_/fct_`; `raw_invoices 38 → stg_invoices 37` is the dedupe.
- **MRR by month** — `1,600 → 1,750 → 1,750 → 1,500`.
- **Current-month movements** — churn −500, contraction −100, expansion +100, new +200, reactivation +50  (Σ = −250).
- **Reconciliations** — revenue: pipeline 1,500 == finance 1,500. MRR identity: closing 1,500 == opening 1,750 + moves −250.
- **Published artifacts** — the 4 CSVs + `_SUCCESS` in `.local_state/gold/`.

Then open one file: `type .local_state\gold\fct_invoice.csv` — amounts in USD; no `billing_email`
or `company_name` column anywhere (hashed / dropped in staging).

## 3. Bad data — the gate earns its keep (45 sec)

```
python -m demo.run --scenario fail        # or: make demo-fail
```

Three things go wrong, handled three different ways:

- **Quality → quarantine.** 2 invoices with a negative amount + 1 with status `bogus` move to
  `reject_fct_invoice`; the run *continues*.
- **Quality → warn.** 1 invoice references plan `PROMO_2024` (not in `dim_plan`) — logged, not blocked.
- **Reconciliation → block.** The run simulates a churn-detection bug (churn movements dropped), so
  closing MRR **1,500** ≠ opening + movements **2,000** → `mrr_movement_identity` breaches 0.1% →
  **PUBLISH BLOCKED**, `gold/` not written, **exit 1**.

Note the contrast: `revenue_vs_finance_gl` still **passes** (1,500 == 1,500). The external check
looked fine; the *internal identity* caught the bug.

### Check the outputs — AFTER the failed run

```
python -m demo.peek
```

- **`reject_fct_invoice`** — the 3 quarantined rows + the rule that caught each.
- **Current-month movements** — no `churn` row (that's the injected bug).
- **Reconciliations** — `mrr_movement_identity` shows closing 1,500 vs opening+moves 2,000.
- **Published artifacts** — *"(none — the run was BLOCKED, nothing published)"*.

"A schema-valid but *wrong* load never reaches finance."

## 4. Any warehouse (20 sec)

- `dbt/models/` — the same SQL as `demo/sql/`, as real dbt models (`fct_mrr_movement` is a
  stub with a TODO pointing back at `demo/sql/20_marts.sql`). `dbt/profiles/profiles.yml` has
  `ci` (DuckDB), `databricks`, `snowflake` targets; `dbt/macros/to_sha256.sql` is the per-engine seam.
- `infra/` — Terraform. `infra/envs/prod/prod.tfvars` is one line: `engine = "snowflake"` —
  flip to `"databricks"` with no model changes.

Close: "Same spec, same gate, same tests — Databricks, Snowflake, or your laptop."

---

## How to see the data — cheat sheet

| moment | command | what you see |
|--------|---------|--------------|
| before | `python -m demo.peek inputs` | source recipe, `control_totals.csv`, `rules.yml` |
| after (either run) | `python -m demo.peek` | row counts, `reject_fct_invoice`, MRR by month, current-month movements, both reconciliations, `gold/` listing |
| after clean | `.local_state\gold\*.csv` (4 tables) + `_SUCCESS` | published marts — USD, no PII |
| after fail | `.local_state\gold\` absent; `reject_fct_invoice` populated | blocked publish + quarantined rows |
| any time | open `.local_state\demo.sqlite` in a SQLite client | the full local warehouse — every layer |

## Reset between runs
Nothing to reset — each run rebuilds `.local_state/` from scratch. `make clean` removes it.
