terraform {
  required_version = ">= 1.6.0"
  # backend "s3" { ... }   # TODO remote state per env
}

variable "engine" {
  type    = string
  default = "duckdb" # dev runs the same models on DuckDB
}

module "pipeline" {
  source = "../../modules/pipeline"

  env            = "dev"
  engine         = var.engine
  landing_bucket = "retail-demo-dev-landing" # TODO real bucket
  warehouse_size = "XSMALL"
}

output "dbt_target"  { value = module.pipeline.dbt_target }
output "catalog_ref" { value = module.pipeline.catalog_ref }
