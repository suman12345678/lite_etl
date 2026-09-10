# infra/bootstrap - run ONCE per AWS account, BEFORE any env.
# Creates the Terraform state backend. No backend block here (local state); the
# outputs feed infra/envs/<env>/backend.tf. ref: deployment-and-iac.md s.3
#
# Phase 4 scaffold - values are TODO / var refs. Do not run terraform here.

terraform {
  required_version = "~> 1.9"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.60" }
  }
}

provider "aws" {
  region = var.region
  # account selected by the caller's AWS profile (shared acct for dev+stg, prd acct for prd)
}

resource "aws_kms_key" "tfstate" {
  description             = "northwind-${var.env}-tfstate CMK"
  deletion_window_in_days = 30
  enable_key_rotation     = true
}

resource "aws_s3_bucket" "tfstate" {
  bucket = "northwind-${var.env}-tfstate" # TODO confirm globally-unique name
}

resource "aws_s3_bucket_versioning" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.tfstate.arn
    }
  }
}

resource "aws_s3_bucket_public_access_block" "tfstate" {
  bucket                  = aws_s3_bucket.tfstate.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_dynamodb_table" "tf_lock" {
  name         = "northwind-tf-lock"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"
  attribute {
    name = "LockID"
    type = "S"
  }
}
