terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
    databricks = {
      source  = "databricks/databricks"
      version = ">= 1.40"
    }
    snowflake = {
      source  = "Snowflake-Labs/snowflake"
      version = ">= 0.90"
    }
  }
}

# Provider auth is never a literal here. aws reads the normal AWS credential
# chain (role in CI/CD, profile locally). databricks reads DATABRICKS_HOST /
# DATABRICKS_TOKEN from the environment. snowflake reads SNOWFLAKE_ACCOUNT /
# SNOWFLAKE_USER / SNOWFLAKE_PASSWORD (or private-key path) from the environment.
# See ../../../README.md for the full env-var list per engine.
provider "aws" {
  region = var.aws_region
}

provider "databricks" {}

provider "snowflake" {}
