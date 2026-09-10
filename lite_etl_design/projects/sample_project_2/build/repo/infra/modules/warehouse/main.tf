# modules/warehouse - Unity Catalog catalog + schemas + grants, the gold_pii
# governance (row filter + column mask + reader group), the pipeline service
# principal and the job compute policy.
# ref: deployment-and-iac.md s.1-2 ; ADR-006 (hashed PII in gold, real in gold_pii)
#
# Phase 4 scaffold - resource blocks named + wired, values are var refs / TODO.

terraform {
  required_providers {
    databricks = { source = "databricks/databricks", version = "~> 1.50" }
  }
}

# Workspace + UC metastore are click-ops (platform team) - this module assumes them.

resource "databricks_catalog" "this" {
  name    = "northwind_${var.env}"
  comment = "Northwind Commerce ${var.env}"
  # storage_root points at the lakehouse external location (storage module output)
  storage_root = var.lakehouse_external_location_url # TODO
}

resource "databricks_schema" "layer" {
  for_each     = toset(["bronze", "silver", "gold", "gold_pii"])
  catalog_name = databricks_catalog.this.name
  name         = each.key
}

resource "databricks_service_principal" "pipeline" {
  display_name = "northwind-${var.env}-pipeline"
}

# --- grants ------------------------------------------------------------------
resource "databricks_grants" "catalog" {
  catalog = databricks_catalog.this.name
  grant {
    principal  = databricks_service_principal.pipeline.application_id
    privileges = ["USE_CATALOG", "USE_SCHEMA", "CREATE_SCHEMA", "MODIFY", "SELECT"]
  }
  grant {
    principal  = var.readers_group # e.g. "northwind_analysts"  # TODO
    privileges = ["USE_CATALOG", "USE_SCHEMA", "SELECT"]
  }
}

# --- gold_pii governance ---------------------------------------------------------
resource "databricks_group" "pii_readers" {
  display_name = "northwind_pii_readers"
}

# Row filter (marketable-consent) + column mask are UC functions; their bodies are
# data-dependent and refined in dbt post-hooks. TODO: create the functions here or
# reference dbt-created ones, then attach:
#   ALTER TABLE gold_pii.dim_customer_pii SET ROW FILTER <fn> ON (marketing_consent);
#   ALTER TABLE gold_pii.dim_customer_pii ALTER COLUMN email SET MASK <fn>;
resource "databricks_grants" "gold_pii" {
  schema = "${databricks_catalog.this.name}.gold_pii"
  grant {
    principal  = databricks_group.pii_readers.display_name
    privileges = ["USE_SCHEMA", "SELECT"]
  }
}

# --- job compute policy --------------------------------------------------------
resource "databricks_cluster_policy" "jobs" {
  name = "northwind-${var.env}-jobs"
  definition = jsonencode({
    "node_type_id" : { "type" : "allowlist", "values" : var.allowed_node_types } # TODO
    "autoscale.min_workers" : { "type" : "fixed", "value" : var.min_workers }
    "autoscale.max_workers" : { "type" : "range", "maxValue" : var.max_workers }
    "spark_version" : { "type" : "regex", "pattern" : "1[0-9]\\..*" } # TODO pin DBR
  })
}
