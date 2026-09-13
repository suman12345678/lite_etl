variable "env" {
  type        = string
  description = "Environment name (dev, prod)."
}

variable "engine" {
  type        = string
  description = "Warehouse the dbt models run on. Pipeline logic does not change with this."
  default     = "duckdb"

  validation {
    condition     = contains(["duckdb", "databricks", "snowflake"], var.engine)
    error_message = "engine must be one of: duckdb, databricks, snowflake."
  }
}

variable "aws_region" {
  type        = string
  description = "AWS region for the landing bucket, ECS cluster, and EventBridge schedules."
}

variable "landing_bucket_name" {
  type        = string
  description = "S3 bucket name where extract/* land raw files (globally unique; set per env)."
}

variable "ecs_cluster_arn" {
  type        = string
  description = "ARN of the existing ECS cluster the scheduled tasks run on."
}

variable "vpc_subnet_ids" {
  type        = list(string)
  description = "Private subnet ids for the Fargate tasks (egress via NAT, no public IP)."
}

variable "security_group_ids" {
  type        = list(string)
  description = "Security group ids for the Fargate tasks (egress to the billing API / CRM DB / warehouse)."
}

variable "pipeline_image_uri" {
  type        = string
  description = "Container image (ECR URI) bundling this repo: extract/, dbt/, orchestration/, rules.yml."
}

variable "billing_api_token_secret_arn" {
  type        = string
  description = "Secrets Manager ARN holding BILLING_API_TOKEN. The value never enters Terraform state."
}

variable "crm_db_password_secret_arn" {
  type        = string
  description = "Secrets Manager ARN holding CRM_DB_PASSWORD."
}

variable "warehouse_secret_arn" {
  type        = string
  description = "Secrets Manager ARN holding the warehouse credential (DATABRICKS_TOKEN or SNOWFLAKE_PASSWORD, per engine). Unused for engine=duckdb."
  default     = null
}

variable "warehouse_size" {
  type        = string
  description = "Compute size for the transform warehouse (engine-specific string, e.g. XSMALL / SMALL)."
  default     = "XSMALL"
}

variable "revenue_recon_tolerance_pct" {
  type        = number
  description = "Reconciliation tolerance for revenue vs GL. Matches rules.yml (revenue_vs_finance_gl)."
  default     = 0.5
}

variable "mrr_recon_tolerance_pct" {
  type        = number
  description = "Reconciliation tolerance for the MRR movement identity. Matches rules.yml (mrr_movement_identity)."
  default     = 0.1
}

variable "schedule_daily_cron" {
  type        = string
  description = "EventBridge cron for the daily full transform+publish run (Schedule: 02:00, deadline 04:00)."
  default     = "cron(0 2 * * ? *)"
}

variable "schedule_hourly_cron" {
  type        = string
  description = "EventBridge cron for the hourly land-only run (Schedule: land new invoices only, no transform/publish)."
  default     = "cron(0 * * * ? *)"
}

variable "log_retention_days" {
  type        = number
  default     = 30
}
