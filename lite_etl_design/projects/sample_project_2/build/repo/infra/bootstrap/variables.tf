variable "env" {
  type        = string
  description = "dev | stg | prd. dev+stg use the shared AWS account; prd is the dedicated locked account."
}

variable "region" {
  type    = string
  default = "eu-west-2"
}
