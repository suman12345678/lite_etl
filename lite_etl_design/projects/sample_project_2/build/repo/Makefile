.PHONY: setup lint test dbt-ci golden clean $(addprefix test-,oltp shopify pos salesforce ga4 fx config secrets landing dbt-runner reconcile publish lineage observability)

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

clean:
	rm -rf .venv .local_state dbt/target dbt/dbt_packages *.duckdb
