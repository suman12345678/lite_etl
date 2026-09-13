# The orchestrator (design.md: "cron, two cadences"). Daily 02:00 runs the full
# extract -> dbt build -> rules gate -> publish. Hourly lands new invoices only
# (Schedule: "an hourly lightweight run that only lands new invoices to raw").

resource "aws_cloudwatch_event_rule" "daily" {
  name                = "${local.name}-daily"
  description         = "projectprod: full transform + publish (Schedule: daily 02:00, deadline 04:00)"
  schedule_expression  = var.schedule_daily_cron
  tags                 = local.tags
}

resource "aws_cloudwatch_event_rule" "hourly" {
  name                = "${local.name}-hourly"
  description         = "projectprod: land-only, new invoices to raw (Schedule: hourly)"
  schedule_expression  = var.schedule_hourly_cron
  tags                 = local.tags
}

resource "aws_cloudwatch_event_target" "daily" {
  rule     = aws_cloudwatch_event_rule.daily.name
  arn      = var.ecs_cluster_arn
  role_arn = aws_iam_role.eventbridge_ecs.arn

  ecs_target {
    task_definition_arn = aws_ecs_task_definition.daily.arn
    task_count           = 1
    launch_type          = "FARGATE"

    network_configuration {
      subnets          = var.vpc_subnet_ids
      security_groups  = var.security_group_ids
      assign_public_ip = false
    }
  }
}

resource "aws_cloudwatch_event_target" "hourly" {
  rule     = aws_cloudwatch_event_rule.hourly.name
  arn      = var.ecs_cluster_arn
  role_arn = aws_iam_role.eventbridge_ecs.arn

  ecs_target {
    task_definition_arn = aws_ecs_task_definition.hourly.arn
    task_count           = 1
    launch_type          = "FARGATE"

    network_configuration {
      subnets          = var.vpc_subnet_ids
      security_groups  = var.security_group_ids
      assign_public_ip = false
    }
  }
}
