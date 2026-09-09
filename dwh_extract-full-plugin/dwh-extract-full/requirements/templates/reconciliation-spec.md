# Reconciliation spec for this source

> Reference: `docs/reconciliation-spec.md`.

- **Row conservation:**      source_rows == landed + rejected + filtered  (hard)
- **Min landed rows:**       >= <n>  (per run / per partition)
- **Control total(s):**      SUM(balance_amount) conserved source -> (landed + rejected), tolerance 0.01
- **Key coverage:**          country_code present in reference `country_codes` for 100% of landed rows
- **No duplicates:**         customer_id unique in landed partition
- **Volume drift:**          landed row count within +/- 25% of trailing-7-run median (warn)
- **Freshness:**             max(source_updated_at) >= run_time - <SLA window>
- **On any hard failure:**   mark run FAILED, do NOT publish, alert <channel>
