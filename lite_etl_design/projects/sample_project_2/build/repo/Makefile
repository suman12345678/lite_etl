.PHONY: setup lint test dbt-ci golden clean dagster-dev tf-fmt $(addprefix test-,oltp shopify pos salesforce ga4 fx config secrets landing dbt-runner reconcile publish lineage observability)

setup:
	uv venv && uv pip install -e ".[dev]"
	cd dbt && dbt deps || true
	pre-commit install || true

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
	python tests/regen_golden.py

# Phase 4 - Dagster code location + Terraform helpers
dagster-dev:
	uv pip install -e ".[dev,orchestration]"
	NORTHWIND_ENV=ci dagster dev -m northwind_dagster

tf-fmt:
	terraform -chdir=infra fmt -recursive

clean:
	rm -rf .venv .local_state dbt/target dbt/dbt_packages *.duckdb
