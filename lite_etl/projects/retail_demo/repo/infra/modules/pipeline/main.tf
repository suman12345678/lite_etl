terraform {
  required_version = ">= 1.6.0"
}

# The only thing that varies between DuckDB / Databricks / Snowflake is this map:
# connection details + the dbt target name. Everything downstream (dbt models,
# rules.yml, the publish gate) is identical.
locals {
  engine_profiles = {
    duckdb = {
      dbt_target   = "ci"
      compute_ref  = "local-process"
      catalog_ref  = "target/retail_demo_ci.duckdb"
    }
    databricks = {
      dbt_target   = "databricks"
      compute_ref  = "sql-warehouse:${var.warehouse_size}" # TODO databricks_sql_endpoint
      catalog_ref  = "unity:retail_demo_${var.env}"        # TODO databricks_schema
    }
    snowflake = {
      dbt_target   = "snowflake"
      compute_ref  = "wh:TRANSFORM_WH_${upper(var.env)}"    # TODO snowflake_warehouse
      catalog_ref  = "RETAIL_DEMO_${upper(var.env)}.MARTS"  # TODO snowflake_schema
    }
  }

  selected = local.engine_profiles[var.engine]

  tags = {
    project = "retail_demo"
    env     = var.env
    engine  = var.engine
  }
}

# Placeholder for the actual deployment resources (warehouse, schema, storage
# grants, the scheduled job). Swap in the provider block for var.engine and the
# resources become real - the interface (outputs) stays the same.
resource "terraform_data" "pipeline" {
  input = {
    env             = var.env
    engine          = var.engine
    dbt_target      = local.selected.dbt_target
    landing_bucket  = var.landing_bucket
    compute         = local.selected.compute_ref
    catalog         = local.selected.catalog_ref
    recon_tol_pct   = var.recon_tolerance_pct
    tags            = local.tags
  }
}
