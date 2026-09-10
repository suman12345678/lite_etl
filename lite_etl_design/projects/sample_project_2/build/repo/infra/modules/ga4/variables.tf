variable "env" { type = string }

variable "gcp_project_id" {
  type    = string
  default = "" # TODO - the GA4 BigQuery export project
}
