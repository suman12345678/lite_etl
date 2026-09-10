# prd - DEDICATED locked AWS account, customer-managed VPC, no public ingress,
# S3 gateway endpoint, VPC peering to the Postgres replica. All values TODO.
region            = "eu-west-2"
databricks_host   = "TODO https://northwind-prd.cloud.databricks.com"
gcp_project_id    = "TODO"
vpc_id            = "TODO customer-managed VPC id"
orchestrator_mode = "cloud_agent"
