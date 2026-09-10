output "dbt_target" {
  description = "dbt target name to pass as --target (see dbt/profiles/profiles.yml)."
  value       = local.selected.dbt_target
}

output "catalog_ref" {
  description = "Where marts land for this engine/env."
  value       = local.selected.catalog_ref
}

output "compute_ref" {
  description = "Transform compute handle for this engine/env."
  value       = local.selected.compute_ref
}

output "landing_bucket" {
  value = var.landing_bucket
}
