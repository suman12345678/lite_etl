# dev overrides. Nothing here is a real account id, ARN, or host -- every value
# is a var.* filled in from your own AWS account / Secrets Manager before `terraform
# apply` (see ../../../README.md "Env vars / tfvars for a real run").
#
#   engine = "duckdb"      # default here, no cloud warehouse
#   engine = "databricks"  # fill dbt/profiles.yml env vars + a warehouse_secret_arn
#   engine = "snowflake"   # fill dbt/profiles.yml env vars + a warehouse_secret_arn
engine = "duckdb"

aws_region          = "us-east-1"
landing_bucket_name = "REPLACE_ME-projectprod-dev-landing"
ecs_cluster_arn     = "REPLACE_ME"   # arn:aws:ecs:<region>:<account>:cluster/<name>
vpc_subnet_ids      = ["REPLACE_ME"]
security_group_ids  = ["REPLACE_ME"]
pipeline_image_uri  = "REPLACE_ME"   # <account>.dkr.ecr.<region>.amazonaws.com/projectprod:<tag>

billing_api_token_secret_arn = "REPLACE_ME"
crm_db_password_secret_arn   = "REPLACE_ME"
warehouse_secret_arn         = null
