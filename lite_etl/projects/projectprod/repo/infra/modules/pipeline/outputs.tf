output "dbt_target" {
  description = "dbt target name to pass as --target (see dbt/profiles/profiles.yml)."
  value       = local.dbt_target
}

output "landing_bucket" {
  description = "S3 bucket extract/* land raw files into."
  value       = aws_s3_bucket.landing.bucket
}

output "pipeline_task_role_arn" {
  value = aws_iam_role.pipeline_task.arn
}

output "daily_task_definition_arn" {
  value = aws_ecs_task_definition.daily.arn
}

output "hourly_task_definition_arn" {
  value = aws_ecs_task_definition.hourly.arn
}

output "databricks_sql_endpoint_id" {
  description = "Set when engine=databricks; feeds DBT_DATABRICKS_HTTP_PATH."
  value       = var.engine == "databricks" ? databricks_sql_endpoint.transform[0].id : null
}

output "databricks_catalog" {
  value = var.engine == "databricks" ? databricks_catalog.projectprod[0].name : null
}

output "snowflake_warehouse" {
  description = "Set when engine=snowflake; feeds DBT_SNOWFLAKE_WAREHOUSE."
  value       = var.engine == "snowflake" ? snowflake_warehouse.transform[0].name : null
}

output "snowflake_database" {
  value = var.engine == "snowflake" ? snowflake_database.projectprod[0].name : null
}
