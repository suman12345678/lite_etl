# Least-privilege role for the scheduled ECS tasks: read/write the landing
# bucket, read only the three named secrets, write logs. No credential value
# lives in this file or in state -- Secrets Manager ARNs only.

data "aws_iam_policy_document" "ecs_tasks_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "pipeline_task" {
  name               = "${local.name}-pipeline-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume.json
  tags               = local.tags
}

data "aws_iam_policy_document" "pipeline_task_policy" {
  statement {
    sid       = "LandingBucketReadWrite"
    actions   = ["s3:GetObject", "s3:PutObject", "s3:ListBucket"]
    resources = [aws_s3_bucket.landing.arn, "${aws_s3_bucket.landing.arn}/*"]
  }

  statement {
    sid = "ReadPipelineSecrets"
    actions = ["secretsmanager:GetSecretValue"]
    resources = compact([
      var.billing_api_token_secret_arn,
      var.crm_db_password_secret_arn,
      var.warehouse_secret_arn,
    ])
  }

  statement {
    sid       = "WriteLogs"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${aws_cloudwatch_log_group.pipeline.arn}:*"]
  }
}

resource "aws_iam_role_policy" "pipeline_task" {
  name   = "${local.name}-pipeline-task-policy"
  role   = aws_iam_role.pipeline_task.id
  policy = data.aws_iam_policy_document.pipeline_task_policy.json
}

resource "aws_cloudwatch_log_group" "pipeline" {
  name              = "/projectprod/${var.env}/pipeline"
  retention_in_days = var.log_retention_days
  tags              = local.tags
}

# EventBridge needs its own role to call ecs:RunTask against the task defs below.
data "aws_iam_policy_document" "events_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "eventbridge_ecs" {
  name               = "${local.name}-eventbridge-ecs"
  assume_role_policy = data.aws_iam_policy_document.events_assume.json
  tags               = local.tags
}

data "aws_iam_policy_document" "eventbridge_ecs_policy" {
  statement {
    sid       = "RunScheduledTasks"
    actions   = ["ecs:RunTask"]
    resources = [aws_ecs_task_definition.daily.arn, aws_ecs_task_definition.hourly.arn]
    condition {
      test     = "ArnEquals"
      variable = "ecs:cluster"
      values   = [var.ecs_cluster_arn]
    }
  }
  statement {
    sid       = "PassPipelineRoles"
    actions   = ["iam:PassRole"]
    resources = [aws_iam_role.pipeline_task.arn]
  }
}

resource "aws_iam_role_policy" "eventbridge_ecs" {
  name   = "${local.name}-eventbridge-ecs-policy"
  role   = aws_iam_role.eventbridge_ecs.id
  policy = data.aws_iam_policy_document.eventbridge_ecs_policy.json
}
