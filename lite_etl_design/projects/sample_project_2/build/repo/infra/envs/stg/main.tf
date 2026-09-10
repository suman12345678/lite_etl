# infra/envs/stg - shared AWS account (same as dev), reuses the dev OIDC provider.
# ref: pipeline/iac-plan.md. Phase 4 scaffold - do not run terraform.

provider "aws" {
  region = var.region
}

provider "databricks" {
  host = var.databricks_host
}

provider "google" {
  project = var.gcp_project_id
}

variable "region" { type = string }
variable "databricks_host" { type = string }
variable "gcp_project_id" { type = string }
variable "vpc_id" { type = string }
variable "orchestrator_mode" {
  type    = string
  default = "cloud_agent"
}

module "ci" {
  source               = "../../modules/ci"
  env                  = "stg"
  create_oidc_provider = false # reuse the provider dev created in the shared account
}

module "storage" {
  source = "../../modules/storage"
  env    = "stg"
}

module "warehouse" {
  source                         = "../../modules/warehouse"
  env                            = "stg"
  lakehouse_external_location_url = module.storage.lakehouse_external_location_url
  min_workers                    = 1
  max_workers                    = 4
}

module "orchestrator" {
  source = "../../modules/orchestrator"
  env    = "stg"
  mode   = var.orchestrator_mode
  vpc_id = var.vpc_id
}

module "ga4" {
  source         = "../../modules/ga4"
  env            = "stg"
  gcp_project_id = var.gcp_project_id
}

module "observability" {
  source = "../../modules/observability"
  env    = "stg"
}

output "config_stg_generated" {
  value = {
    catalog                 = module.warehouse.catalog_name
    storage                 = module.storage.bucket_uris
    orchestrator_deployment = module.orchestrator.deployment_name
    orchestrator_mode       = module.orchestrator.mode
    alerts_topic_arn        = module.observability.alerts_topic_arn
    ci_role_arn             = module.ci.ci_role_arn
  }
}
