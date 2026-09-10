# infra/envs/dev - wires the modules in apply order for the dev environment.
# ref: pipeline/iac-plan.md "Apply order". Values come from dev.tfvars.
# Phase 4 scaffold - do not run terraform.

provider "aws" {
  region = var.region
}

provider "databricks" {
  host = var.databricks_host # TODO
}

provider "google" {
  project = var.gcp_project_id # TODO
}

variable "region" { type = string }
variable "databricks_host" { type = string }
variable "gcp_project_id" { type = string }
variable "vpc_id" { type = string }
variable "orchestrator_mode" {
  type    = string
  default = "cloud_agent"
}

# 2. ci (OIDC) - first so pipelines can assume the role
module "ci" {
  source               = "../../modules/ci"
  env                  = "dev"
  create_oidc_provider = true # dev creates it; stg reuses (shared account)
}

# 3. storage -> warehouse -> orchestrator -> ga4 -> observability
module "storage" {
  source = "../../modules/storage"
  env    = "dev"
}

module "warehouse" {
  source                         = "../../modules/warehouse"
  env                            = "dev"
  lakehouse_external_location_url = module.storage.lakehouse_external_location_url
  min_workers                    = 1
  max_workers                    = 2 # dev: 1-2 spot
}

module "orchestrator" {
  source = "../../modules/orchestrator"
  env    = "dev"
  mode   = var.orchestrator_mode
  vpc_id = var.vpc_id
}

module "ga4" {
  source         = "../../modules/ga4"
  env            = "dev"
  gcp_project_id = var.gcp_project_id
}

module "observability" {
  source = "../../modules/observability"
  env    = "dev"
}

# 4. `terraform output -json` -> scripts/tf_to_config.py -> config/dev.generated.yml
output "config_dev_generated" {
  value = {
    catalog                 = module.warehouse.catalog_name
    storage                 = module.storage.bucket_uris
    orchestrator_deployment = module.orchestrator.deployment_name
    orchestrator_mode       = module.orchestrator.mode
    alerts_topic_arn        = module.observability.alerts_topic_arn
    ci_role_arn             = module.ci.ci_role_arn
  }
}
