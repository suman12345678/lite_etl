variable "env" { type = string }

variable "lakehouse_external_location_url" {
  type        = string
  description = "s3://northwind-<env>-lakehouse/... - from the storage module output"
  default     = "" # TODO
}

variable "readers_group" {
  type    = string
  default = "" # TODO e.g. northwind_analysts
}

variable "allowed_node_types" {
  type    = list(string)
  default = [] # TODO
}

variable "min_workers" {
  type    = number
  default = 1
}

variable "max_workers" {
  type    = number
  default = 4 # dev overridden to 2 (spot) in dev.tfvars
}
