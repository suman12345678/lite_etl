output "tfstate_bucket" {
  value = aws_s3_bucket.tfstate.id
}

output "tf_lock_table" {
  value = aws_dynamodb_table.tf_lock.name
}

output "tfstate_kms_key_arn" {
  value = aws_kms_key.tfstate.arn
}
