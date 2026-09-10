variable "env" { type = string }

variable "inbound_retention_days" {
  type    = number
  default = 30 # TODO tune per env
}

variable "uc_access_role_arn" {
  type        = string
  description = "IAM role Unity Catalog assumes to read the lakehouse bucket"
  default     = "" # TODO
}
