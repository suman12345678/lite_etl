# prod overrides. Same module, same models, same rules.yml -- only this changes.
# Nothing here is a real account id, ARN, or host -- fill every REPLACE_ME from
# your own AWS account / Secrets Manager before `terraform apply` (see
# ../../../README.md "Env vars / tfvars for a real run").
engine = "snowflake"

aws_region          = "us-east-1"
landing_bucket_name = "REPLACE_ME-projectprod-prod-landing"
ecs_cluster_arn     = "REPLACE_ME"
vpc_subnet_ids      = ["REPLACE_ME"]
security_group_ids  = ["REPLACE_ME"]
pipeline_image_uri  = "REPLACE_ME"

billing_api_token_secret_arn = "REPLACE_ME"
crm_db_password_secret_arn   = "REPLACE_ME"
warehouse_secret_arn         = "REPLACE_ME"
