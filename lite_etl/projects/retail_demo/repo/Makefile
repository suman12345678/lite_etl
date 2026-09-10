PY ?= python

.PHONY: setup demo demo-fail peek-inputs peek dbt-ci tf-validate test clean

setup:             ## create .venv and install the demo runtime (PyYAML)
	$(PY) -m venv .venv
	.venv/Scripts/python -m pip install -r requirements.txt

# --- the two-minute stage demo (no cloud) ------------------------------------
peek-inputs:       ## check BEFORE: source recipe, rules.yml, finance control totals
	$(PY) -m demo.peek inputs

demo:              ## clean run: all checks pass -> publishes .local_state/gold/
	$(PY) -m demo.run --scenario clean

demo-fail:         ## bad data: quality quarantines rows, reconcile BLOCKS publish, exit 1
	$(PY) -m demo.run --scenario fail

peek:              ## check AFTER: row counts, quarantine, reconcile, published gold/
	$(PY) -m demo.peek

# --- the same logic on a real warehouse -------------------------------------
dbt-ci:            ## build + test the dbt slice on DuckDB (needs: pip install dbt-duckdb dbt-utils)
	cd dbt && dbt deps && dbt seed --target ci && dbt build --target ci

tf-validate:       ## validate the Terraform (needs: terraform)
	cd infra/envs/dev && terraform init -backend=false && terraform validate

test: demo demo-fail-expected-1

demo-fail-expected-1:
	@$(PY) -m demo.run --scenario fail; test $$? -eq 1 && echo "demo-fail correctly exited 1"

clean:
	rm -rf .local_state dbt/target dbt/dbt_packages
