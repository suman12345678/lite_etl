output "bucket_names" {
  value = { for k, b in aws_s3_bucket.this : k => b.id }
}

output "bucket_uris" {
  value = { for k, b in aws_s3_bucket.this : k => "s3://${b.id}" }
}

output "lakehouse_external_location_url" {
  value = databricks_external_location.lakehouse.url
}

output "lakehouse_kms_key_arn" {
  value = aws_kms_key.lakehouse.arn
}
