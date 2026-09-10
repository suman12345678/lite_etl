variable "env" { type = string }

variable "github_repo" {
  type    = string
  default = "northwind/northwind-data"
}

variable "create_oidc_provider" {
  type        = bool
  default     = true # true in the first env of an account, false in the rest
  description = "One OIDC provider per AWS account; reuse it in the other envs."
}
