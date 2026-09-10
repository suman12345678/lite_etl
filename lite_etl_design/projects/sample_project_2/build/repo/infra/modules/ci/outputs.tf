output "ci_role_arn" {
  value = aws_iam_role.ci.arn
}

output "runner_instance_profile" {
  value = aws_iam_instance_profile.runner.name
}
