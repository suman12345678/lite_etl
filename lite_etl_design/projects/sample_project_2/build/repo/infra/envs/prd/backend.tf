terraform {
  required_version = "~> 1.9"

  # prd state lives in the DEDICATED LOCKED prd AWS account.
  backend "s3" {
    bucket         = "northwind-prd-tfstate"
    key            = "prd/terraform.tfstate"
    region         = "eu-west-2"
    dynamodb_table = "northwind-tf-lock"
    encrypt        = true
    # kms_key_id   = "TODO prd tfstate CMK arn from bootstrap (prd account)"
  }

  required_providers {
    aws        = { source = "hashicorp/aws", version = "~> 5.60" }
    databricks = { source = "databricks/databricks", version = "~> 1.50" }
    google     = { source = "hashicorp/google", version = "~> 5.40" }
  }
}
