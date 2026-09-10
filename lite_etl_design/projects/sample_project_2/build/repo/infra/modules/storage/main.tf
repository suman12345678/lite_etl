# modules/storage - S3 buckets (inbound / lakehouse / dbt-docs), lifecycle,
# SSE-KMS, and the Databricks external location + storage credential that let UC
# read the lakehouse bucket.
# ref: deployment-and-iac.md s.1
#
# Phase 4 scaffold - values are var refs / TODO.

terraform {
  required_providers {
    aws        = { source = "hashicorp/aws", version = "~> 5.60" }
    databricks = { source = "databricks/databricks", version = "~> 1.50" }
  }
}

resource "aws_kms_key" "lakehouse" {
  description         = "northwind-${var.env}-lakehouse CMK"
  enable_key_rotation = true
}

locals {
  buckets = {
    inbound   = "northwind-${var.env}-inbound"
    lakehouse = "northwind-${var.env}-lakehouse"
    dbt_docs  = "northwind-${var.env}-dbt-docs"
  }
}

resource "aws_s3_bucket" "this" {
  for_each = local.buckets
  bucket   = each.value # TODO confirm globally unique
}

resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  for_each = aws_s3_bucket.this
  bucket   = each.value.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.lakehouse.arn
    }
  }
}

resource "aws_s3_bucket_public_access_block" "this" {
  for_each                = aws_s3_bucket.this
  bucket                  = each.value.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "inbound" {
  bucket = aws_s3_bucket.this["inbound"].id
  rule {
    id     = "expire-landed-pos"
    status = "Enabled"
    expiration { days = var.inbound_retention_days } # TODO
  }
}

# --- UC external access to the lakehouse bucket -------------------------------
resource "databricks_storage_credential" "lakehouse" {
  name = "northwind-${var.env}-lakehouse"
  aws_iam_role {
    role_arn = var.uc_access_role_arn # TODO - role UC assumes to read the bucket
  }
}

resource "databricks_external_location" "lakehouse" {
  name            = "northwind-${var.env}-lakehouse"
  url             = "s3://${aws_s3_bucket.this["lakehouse"].id}/"
  credential_name = databricks_storage_credential.lakehouse.name
}
