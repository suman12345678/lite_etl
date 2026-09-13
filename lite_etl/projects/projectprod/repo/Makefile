PY ?= python
ENV ?= dev

.PHONY: setup peek-inputs demo peek demo-fail dbt-ci tf-validate test test-extract \
        extract-billing extract-crm extract-ref deploy clean

setup:             ## create .venv and install the demo runtime (PyYAML)
	$(PY) -m venv .venv
	.venv/Scripts/python -m pip install -r requirements.txt

# --- the two-minute stage demo (no cloud) ----------------------------------
peek-inputs:       ## check BEFORE: source recipe, rules.yml, finance control totals
	$(PY) -m demo.peek inputs

demo:              ## clean run: all checks pass -> publishes .local_state/gold/
	$(PY) -m demo.run --scenario clean

peek:              ## check AFTER: row counts, quarantine, MRR, reconciliations, gold/
	$(PY) -m demo.peek

demo-fail:         ## bad data: quality quarantines rows, MRR identity BLOCKS publish, exit 1
	$(PY) -m demo.run --scenario fail

test:
	$(PY) -m demo.run --scenario clean
	@$(PY) -m demo.run --scenario fail; test $$? -eq 1 && echo "demo-fail correctly exited 1"

# --- the same logic on a real warehouse ----------------------------------
dbt-ci:            ## seed a DuckDB raw schema from the demo fixture, then build+test every model
	$(PY) dbt/seed_ci_raw.py
	cd dbt && dbt deps && dbt seed --target ci && dbt build --target ci

tf-validate:       ## validate the Terraform (needs: terraform)
	cd infra/envs/dev && terraform init -backend=false && terraform validate

# --- extractors (need requirements-extract.txt + real credentials/env vars) --
test-extract:      ## extractor unit tests against recorded fixtures, no live creds
	$(PY) -m unittest discover -s tests -v

extract-billing:   ## land billing.invoices + billing.subscriptions (needs BILLING_API_*)
	$(PY) -m extract.billing --mode daily

extract-crm:       ## land the daily crm.accounts snapshot (needs CRM_DB_*)
	$(PY) -m extract.crm

extract-ref:       ## land ref.plans + ref.fx_rates (needs REF_S3_BUCKET, AWS creds)
	$(PY) -m extract.ref

# --- deploy ------------------------------------------------------------------
deploy:            ## terraform apply for ENV=dev|prod (needs infra/envs/$(ENV)/*.tfvars filled in)
	cd infra/envs/$(ENV) && terraform init && terraform apply -var-file=$(ENV).tfvars

clean:
	rm -rf .local_state gold dbt/target dbt/dbt_packages
