terraform {
  required_version = "~> 1.9"

  backend "s3" {
    bucket         = "northwind-dev-tfstate" # from infra/bootstrap output
    key            = "dev/terraform.tfstate"
    region         = "eu-west-2"
    dynamodb_table = "northwind-tf-lock"
    encrypt        = true
    # kms_key_id   = "TODO tfstate CMK arn from bootstrap"
  }

  required_providers {
    aws        = { source = "hashicorp/aws", version = "~> 5.60" }
    databricks = { source = "databricks/databricks", version = "~> 1.50" }
    google     = { source = "hashicorp/google", version = "~> 5.40" }
  }
}
