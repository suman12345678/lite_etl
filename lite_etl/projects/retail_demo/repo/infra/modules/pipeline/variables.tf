variable "env" {
  type        = string
  description = "Environment name (dev, prod)."
}

variable "engine" {
  type        = string
  description = "Warehouse the dbt models run on. The pipeline logic does not change with this."
  default     = "duckdb"

  validation {
    condition     = contains(["duckdb", "databricks", "snowflake"], var.engine)
    error_message = "engine must be one of: duckdb, databricks, snowflake."
  }
}

variable "landing_bucket" {
  type        = string
  description = "Object-store bucket/volume where extract/* land raw files. TODO: real name per env."
}

variable "warehouse_size" {
  type        = string
  description = "Compute size for the transform warehouse (engine-specific string)."
  default     = "XSMALL"
}

variable "recon_tolerance_pct" {
  type        = number
  description = "Reconciliation tolerance passed through to the publish gate. Matches rules.yml."
  default     = 0.5
}
