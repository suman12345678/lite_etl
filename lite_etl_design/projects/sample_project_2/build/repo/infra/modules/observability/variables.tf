variable "env" { type = string }

variable "monthly_budget_usd" {
  type    = number
  default = 6000 # requirements/09 - < $6k/mo
}

variable "pagerduty_endpoint" {
  type    = string
  default = "" # TODO - https integration URL, sourced from Secrets Manager
}
