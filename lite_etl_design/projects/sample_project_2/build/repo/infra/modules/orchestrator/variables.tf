variable "env" { type = string }

variable "mode" {
  type    = string
  default = "cloud_agent" # cloud_agent | oss_selfhost  (Q3 / ADR-005)
  validation {
    condition     = contains(["cloud_agent", "oss_selfhost"], var.mode)
    error_message = "mode must be cloud_agent or oss_selfhost."
  }
}

variable "vpc_id" {
  type    = string
  default = "" # TODO - shared VPC (dev/stg) or customer-managed VPC (prd)
}

variable "web_desired_count" {
  type    = number
  default = 1
}

variable "run_worker_max" {
  type    = number
  default = 4
}
