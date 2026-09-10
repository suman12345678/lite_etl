output "catalog_name" {
  value = databricks_catalog.this.name
}

output "pipeline_sp_application_id" {
  value = databricks_service_principal.pipeline.application_id
}

output "job_cluster_policy_id" {
  value = databricks_cluster_policy.jobs.id
}

output "pii_readers_group" {
  value = databricks_group.pii_readers.display_name
}
