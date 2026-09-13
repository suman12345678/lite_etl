#!/usr/bin/env bash
# Hourly land-only run (Schedule: "an hourly lightweight run that only lands new
# invoices to raw (no transform, no publish)"). Deliberately does not touch dbt,
# rules.yml, or publish -- just extract/billing in hourly mode.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

: "${ENGINE:?set ENGINE=duckdb|databricks|snowflake}"

echo "== extract/billing --mode hourly (land-only, invoices) =="
python -m extract.billing --mode hourly
