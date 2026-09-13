locals {
  name = "projectprod-${var.env}"

  # The only thing that varies between DuckDB / Databricks / Snowflake is the
  # dbt target + where marts land (warehouse.tf). Everything else here --
  # landing storage, IAM, the ECS task definitions, the two EventBridge
  # schedules -- is identical across engines.
  dbt_target = {
    duckdb     = "ci"
    databricks = "databricks"
    snowflake  = "snowflake"
  }[var.engine]

  tags = {
    project = "projectprod"
    env     = var.env
    engine  = var.engine
  }
}
