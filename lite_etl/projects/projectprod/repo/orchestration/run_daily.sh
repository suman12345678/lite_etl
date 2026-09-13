#!/usr/bin/env bash
# Daily 02:00 run (Schedule: "daily 02:00, after the FX file and the CRM
# snapshot land; deadline 04:00"): full extract -> dbt build -> rules gate ->
# publish, or block and exit 1. Run inside the pipeline container (see
# ../infra/modules/pipeline/ecs.tf) or any host with this repo + its Python deps
# installed and ENGINE/credentials set as environment variables.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

: "${ENGINE:?set ENGINE=duckdb|databricks|snowflake}"
: "${DBT_TARGET:?set DBT_TARGET to match dbt/profiles/profiles.yml (ci|databricks|snowflake)}"

echo "== extract/billing (invoices + subscriptions) =="
python -m extract.billing --mode daily

echo "== extract/crm (daily accounts snapshot) =="
python -m extract.crm

echo "== extract/ref (plans + fx_rates) =="
python -m extract.ref

echo "== dbt build --target ${DBT_TARGET} =="
(cd dbt && dbt deps && dbt seed --target "${DBT_TARGET}" && dbt build --target "${DBT_TARGET}")

echo "== rules gate + publish =="
python -m publish.gate --mode publish
