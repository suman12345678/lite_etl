terraform {
  required_version = ">= 1.6.0"
  # backend "s3" {}   # configure via -backend-config, e.g. `terraform init
  #                      -backend-config="bucket=$TF_STATE_BUCKET" -backend-config="key=projectprod/prod.tfstate"`
}

variable "engine" {
  type    = string
  default = "snowflake" # placeholder prod target -- spec.md Open questions: not yet decided
                         # vs "databricks"; flip here without touching any model
}

variable "aws_region" {
  type = string
}

variable "landing_bucket_name" {
  type = string
}

variable "ecs_cluster_arn" {
  type = string
}

variable "vpc_subnet_ids" {
  type = list(string)
}

variable "security_group_ids" {
  type = list(string)
}

variable "pipeline_image_uri" {
  type = string
}

variable "billing_api_token_secret_arn" {
  type = string
}

variable "crm_db_password_secret_arn" {
  type = string
}

variable "warehouse_secret_arn" {
  type = string
}

module "pipeline" {
  source = "../../modules/pipeline"

  env                          = "prod"
  engine                       = var.engine
  aws_region                   = var.aws_region
  landing_bucket_name          = var.landing_bucket_name
  ecs_cluster_arn              = var.ecs_cluster_arn
  vpc_subnet_ids               = var.vpc_subnet_ids
  security_group_ids           = var.security_group_ids
  pipeline_image_uri           = var.pipeline_image_uri
  billing_api_token_secret_arn = var.billing_api_token_secret_arn
  crm_db_password_secret_arn   = var.crm_db_password_secret_arn
  warehouse_secret_arn         = var.warehouse_secret_arn
  warehouse_size               = "SMALL"
}

output "dbt_target" {
  value = module.pipeline.dbt_target
}

output "landing_bucket" {
  value = module.pipeline.landing_bucket
}
