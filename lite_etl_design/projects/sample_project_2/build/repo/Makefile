PY ?= python

.PHONY: setup demo demo-good demo-fixed demo-fail lint test dbt-ci golden clean dagster-dev tf-fmt $(addprefix test-,oltp shopify pos salesforce ga4 fx config secrets landing dbt-runner reconcile publish lineage observability)

setup:
	uv venv && uv pip install -e ".[dev]"
	cd dbt && dbt deps || true
	pre-commit install || true

# --- runnable local demo (no cloud, no dbt, no Dagster) - see DEMO.md ----------
# load synthetic fixtures -> transform -> DQ quarantine -> reconciliation gate -> publish
demo:                        ## bad data: DQ quarantines the bad row, reconciliation PASS, publish
	$(PY) -m demo.run --dataset bad --control-totals pass
demo-good:                   ## clean data, nothing quarantined
	$(PY) -m demo.run --dataset good
demo-fixed:                  ## the quarantined row corrected at source, re-run green
	$(PY) -m demo.run --dataset fixed
demo-fail:                   ## force a reconciliation FAIL -> publish blocked, exit 1
	$(PY) -m demo.run --dataset bad --control-totals fail

lint:
	ruff check . && sqlfluff lint dbt/models || true
	mypy extractors recon publish lineage obs || true

test:
	pytest
	$(MAKE) dbt-ci

test-%:
	pytest tests/unit/test_$*.py

dbt-ci:
	cd dbt && dbt build --target ci

golden:
	$(PY) tests/regen_golden.py

# Phase 4 - Dagster code location + Terraform helpers
dagster-dev:
	uv pip install -e ".[dev,orchestration]"
	NORTHWIND_ENV=ci dagster dev -m northwind_dagster

tf-fmt:
	terraform -chdir=infra fmt -recursive

clean:
	rm -rf .venv .local_state dbt/target dbt/dbt_packages *.duckdb
