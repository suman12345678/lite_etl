output "ecs_cluster_arn" {
  value = aws_ecs_cluster.this.arn
}

output "task_role_arn" {
  value = aws_iam_role.task.arn
}

output "deployment_name" {
  value = "northwind-${var.env}"
}

output "mode" {
  value = var.mode
}
