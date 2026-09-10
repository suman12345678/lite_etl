# infra/envs/prd - DEDICATED locked AWS account, customer-managed VPC, no public
# ingress. Its own OIDC provider. photon on curated_build + on-demand backfill
# pool. ref: pipeline/iac-plan.md + deployment-and-iac.md s.8.
# Phase 4 scaffold - do not run terraform. prd apply needs 2 approvers + change window.

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
  env                  = "prd"
  create_oidc_provider = true # prd account has its own provider
}

module "storage" {
  source                 = "../../modules/storage"
  env                    = "prd"
  inbound_retention_days = 90
}

module "warehouse" {
  source                         = "../../modules/warehouse"
  env                            = "prd"
  lakehouse_external_location_url = module.storage.lakehouse_external_location_url
  min_workers                    = 1
  max_workers                    = 4 # + photon on curated_build + on-demand backfill pool (TODO in module)
}

module "orchestrator" {
  source = "../../modules/orchestrator"
  env    = "prd"
  mode   = var.orchestrator_mode
  vpc_id = var.vpc_id # customer-managed VPC, private subnets only
}

module "ga4" {
  source         = "../../modules/ga4"
  env            = "prd"
  gcp_project_id = var.gcp_project_id
}

module "observability" {
  source             = "../../modules/observability"
  env                = "prd"
  monthly_budget_usd = 6000
}

output "config_prd_generated" {
  value = {
    catalog                 = module.warehouse.catalog_name
    storage                 = module.storage.bucket_uris
    orchestrator_deployment = module.orchestrator.deployment_name
    orchestrator_mode       = module.orchestrator.mode
    alerts_topic_arn        = module.observability.alerts_topic_arn
    ci_role_arn             = module.ci.ci_role_arn
  }
}
