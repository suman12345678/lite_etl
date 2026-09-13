#!/usr/bin/env bash
# Backfill: re-run one month at a time. `publish.gate` replaces that month's
# rows in every gold table (Schedule: "backfill: --date-range <start> <end>
# re-runs one month at a time; publish is idempotent replace per month").
#
#   ./orchestration/run_backfill.sh 2026-05 2026-06
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

: "${ENGINE:?set ENGINE=duckdb|databricks|snowflake}"
: "${DBT_TARGET:?set DBT_TARGET to match dbt/profiles/profiles.yml}"

start="${1:?usage: run_backfill.sh <start-month YYYY-MM> <end-month YYYY-MM>}"
end="${2:?usage: run_backfill.sh <start-month YYYY-MM> <end-month YYYY-MM>}"

echo "== dbt build --target ${DBT_TARGET} (re-derive staging/intermediate/marts) =="
(cd dbt && dbt deps && dbt seed --target "${DBT_TARGET}" && dbt build --target "${DBT_TARGET}")

echo "== rules gate + idempotent replace-per-month publish for ${start}..${end} =="
python -m publish.gate --mode publish --date-range "${start}" "${end}"
