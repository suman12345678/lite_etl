# dev - shared AWS account, shared VPC, public control plane. All values TODO.
region            = "eu-west-2"
databricks_host   = "TODO https://northwind-dev.cloud.databricks.com"
gcp_project_id    = "TODO"
vpc_id            = "TODO shared VPC id"
orchestrator_mode = "cloud_agent" # Q3 - flip to oss_selfhost if InfoSec rejects Dagster Cloud
