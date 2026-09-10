terraform {
  required_version = ">= 1.6.0"
  # backend "s3" { ... }   # TODO remote state per env
}

variable "engine" {
  type    = string
  default = "snowflake" # prod target - flip to "databricks" without touching any model
}

module "pipeline" {
  source = "../../modules/pipeline"

  env            = "prod"
  engine         = var.engine
  landing_bucket = "project2-prod-landing" # TODO real bucket
  warehouse_size = "SMALL"
}

output "dbt_target"  { value = module.pipeline.dbt_target }
output "catalog_ref" { value = module.pipeline.catalog_ref }
