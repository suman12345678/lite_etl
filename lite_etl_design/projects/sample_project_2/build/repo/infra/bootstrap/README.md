# infra/bootstrap

Run **once per AWS account**, before any `infra/envs/<env>`:

```
cd infra/bootstrap
terraform init                     # local state - not committed anywhere
terraform apply -var env=dev       # shared account: covers dev + stg
terraform apply -var env=prd       # dedicated locked prd account (switch AWS profile first)
```

Outputs (`tfstate_bucket`, `tf_lock_table`, `tfstate_kms_key_arn`) are copied
into `infra/envs/<env>/backend.tf`. After that, every env uses the S3 backend.

This directory is intentionally backend-less. Do not add a `backend "s3"` block.
ref: `pipeline/iac-plan.md` "State backend bootstrap".
