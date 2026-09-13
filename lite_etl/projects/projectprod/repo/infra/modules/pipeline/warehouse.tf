# The only resources that differ per engine: compute + catalog/schema. Chosen by
# var.engine (spec.md Open questions: prod engine not yet decided between
# Databricks and Snowflake) -- dbt models, rules.yml, and the orchestrator above
# are unchanged either way. engine=duckdb (dev/CI) needs no cloud resource here.

# ---------------------------------------------------------------------------
# Databricks
# ---------------------------------------------------------------------------
resource "databricks_sql_endpoint" "transform" {
  count            = var.engine == "databricks" ? 1 : 0
  name             = "${local.name}-transform"
  cluster_size     = var.warehouse_size
  auto_stop_mins   = 30
  max_num_clusters = var.env == "prod" ? 4 : 1
  tags {
    custom_tags {
      key   = "project"
      value = "projectprod"
    }
    custom_tags {
      key   = "env"
      value = var.env
    }
  }
}

resource "databricks_catalog" "projectprod" {
  count   = var.engine == "databricks" ? 1 : 0
  name    = "projectprod_${var.env}"
  comment = "projectprod subscription-revenue pipeline (raw + marts schemas)."
}

resource "databricks_schema" "raw" {
  count        = var.engine == "databricks" ? 1 : 0
  catalog_name = databricks_catalog.projectprod[0].name
  name         = "raw"
  comment      = "Landed by extract/billing.py, extract/crm.py, extract/ref.py."
}

resource "databricks_schema" "marts" {
  count        = var.engine == "databricks" ? 1 : 0
  catalog_name = databricks_catalog.projectprod[0].name
  name         = "marts"
  comment      = "dbt marts: dim_account, dim_plan, fct_invoice, fct_mrr_movement."
}

# ---------------------------------------------------------------------------
# Snowflake
# ---------------------------------------------------------------------------
resource "snowflake_warehouse" "transform" {
  count                = var.engine == "snowflake" ? 1 : 0
  name                 = "PROJECTPROD_${upper(var.env)}_TRANSFORM_WH"
  warehouse_size       = var.warehouse_size
  auto_suspend         = 60
  auto_resume          = true
  initially_suspended  = true
}

resource "snowflake_database" "projectprod" {
  count   = var.engine == "snowflake" ? 1 : 0
  name    = "PROJECTPROD_${upper(var.env)}"
  comment = "projectprod subscription-revenue pipeline."
}

resource "snowflake_schema" "raw" {
  count    = var.engine == "snowflake" ? 1 : 0
  database = snowflake_database.projectprod[0].name
  name     = "RAW"
  comment  = "Landed by extract/billing.py, extract/crm.py, extract/ref.py."
}

resource "snowflake_schema" "marts" {
  count    = var.engine == "snowflake" ? 1 : 0
  database = snowflake_database.projectprod[0].name
  name     = "MARTS"
  comment  = "dbt marts: dim_account, dim_plan, fct_invoice, fct_mrr_movement."
}

resource "snowflake_role" "transformer" {
  count   = var.engine == "snowflake" ? 1 : 0
  name    = "PROJECTPROD_${upper(var.env)}_TRANSFORMER"
  comment = "Role dbt/profiles/profiles.yml's snowflake target assumes."
}

resource "snowflake_grant_privileges_to_role" "warehouse_usage" {
  count             = var.engine == "snowflake" ? 1 : 0
  role_name         = snowflake_role.transformer[0].name
  privileges        = ["USAGE", "OPERATE"]
  on_account_object {
    object_type = "WAREHOUSE"
    object_name = snowflake_warehouse.transform[0].name
  }
}

resource "snowflake_grant_privileges_to_role" "schema_all" {
  count             = var.engine == "snowflake" ? 1 : 0
  role_name         = snowflake_role.transformer[0].name
  privileges        = ["SELECT", "INSERT", "UPDATE", "DELETE"]
  on_schema_object {
    all {
      object_type_plural = "TABLES"
      in_schema           = "${snowflake_database.projectprod[0].name}.${snowflake_schema.marts[0].name}"
    }
  }
}
