# modules/orchestrator - the Dagster deployment on ECS Fargate.
#   var.mode = "cloud_agent"  -> Dagster Cloud hybrid agent (default; Q3 / ADR-005)
#   var.mode = "oss_selfhost" -> Dagster OSS webserver + daemon services
# Asset code (northwind_dagster/) is identical in both modes.
# ref: deployment-and-iac.md s.2 ; requirements/07
#
# Phase 4 scaffold - VPC lookups + ECS/ALB/IAM named, values are var refs / TODO.

terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.60" }
  }
}

data "aws_vpc" "this" { id = var.vpc_id }                 # TODO
data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [var.vpc_id]
  }
  tags = { Tier = "private" } # TODO
}

resource "aws_ecs_cluster" "this" {
  name = "northwind-${var.env}-orchestration"
}

resource "aws_iam_role" "task" {
  name               = "northwind-${var.env}-dagster-task"
  assume_role_policy = data.aws_iam_policy_document.task_assume.json
}

data "aws_iam_policy_document" "task_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

# TODO least-privilege: S3 (buckets from storage module), Secrets Manager
# (northwind/<env>/*), Databricks token via secret, CloudWatch logs.
resource "aws_iam_role_policy" "task" {
  role   = aws_iam_role.task.id
  policy = jsonencode({ Version = "2012-10-17", Statement = [] }) # TODO
}

resource "aws_security_group" "agent" {
  name   = "northwind-${var.env}-dagster"
  vpc_id = var.vpc_id
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"] # TODO tighten (Databricks + Dagster Cloud + S3 endpoint)
  }
}

# --- cloud_agent -------------------------------------------------------------
resource "aws_ecs_service" "agent" {
  count           = var.mode == "cloud_agent" ? 1 : 0
  name            = "dagster-cloud-agent"
  cluster         = aws_ecs_cluster.this.id
  desired_count   = 1
  launch_type     = "FARGATE"
  task_definition = "TODO" # aws_ecs_task_definition.agent[0].arn
  network_configuration {
    subnets         = data.aws_subnets.private.ids
    security_groups = [aws_security_group.agent.id]
  }
}

# --- oss_selfhost (webserver + daemon + ALB) --------------------------------
resource "aws_lb" "web" {
  count              = var.mode == "oss_selfhost" ? 1 : 0
  name               = "northwind-${var.env}-dagster"
  internal           = true
  load_balancer_type = "application"
  subnets            = data.aws_subnets.private.ids
  security_groups    = [aws_security_group.agent.id]
}

resource "aws_ecs_service" "webserver" {
  count           = var.mode == "oss_selfhost" ? 1 : 0
  name            = "dagster-webserver"
  cluster         = aws_ecs_cluster.this.id
  desired_count   = var.web_desired_count
  launch_type     = "FARGATE"
  task_definition = "TODO"
  network_configuration {
    subnets         = data.aws_subnets.private.ids
    security_groups = [aws_security_group.agent.id]
  }
}

resource "aws_ecs_service" "daemon" {
  count           = var.mode == "oss_selfhost" ? 1 : 0
  name            = "dagster-daemon"
  cluster         = aws_ecs_cluster.this.id
  desired_count   = 1
  launch_type     = "FARGATE"
  task_definition = "TODO"
  network_configuration {
    subnets         = data.aws_subnets.private.ids
    security_groups = [aws_security_group.agent.id]
  }
}

resource "aws_appautoscaling_target" "runs" {
  count              = var.mode == "oss_selfhost" ? 1 : 0
  max_capacity       = var.run_worker_max
  min_capacity       = 0
  resource_id        = "service/${aws_ecs_cluster.this.name}/dagster-daemon"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}
