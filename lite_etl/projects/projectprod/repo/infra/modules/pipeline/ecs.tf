# One container image (pipeline_image_uri, built from this repo's Dockerfile-
# equivalent: extract/, dbt/, orchestration/, rules.yml), two Fargate task
# definitions -- one command per Schedule cadence. EventBridge (schedule.tf)
# is the orchestrator design.md names: cron, two cadences.

locals {
  warehouse_secret_env_name = {
    duckdb     = null
    databricks = "DATABRICKS_TOKEN"
    snowflake  = "SNOWFLAKE_PASSWORD"
  }[var.engine]

  pipeline_secrets = concat(
    [
      { name = "BILLING_API_TOKEN", valueFrom = var.billing_api_token_secret_arn },
      { name = "CRM_DB_PASSWORD", valueFrom = var.crm_db_password_secret_arn },
    ],
    var.warehouse_secret_arn != null ? [
      { name = local.warehouse_secret_env_name, valueFrom = var.warehouse_secret_arn }
    ] : []
  )

  pipeline_environment = [
    { name = "ENGINE", value = var.engine },
    { name = "DBT_TARGET", value = local.dbt_target },
    { name = "AWS_REGION", value = var.aws_region },
    { name = "REF_S3_BUCKET", value = aws_s3_bucket.landing.bucket },
    { name = "REVENUE_RECON_TOLERANCE_PCT", value = tostring(var.revenue_recon_tolerance_pct) },
    { name = "MRR_RECON_TOLERANCE_PCT", value = tostring(var.mrr_recon_tolerance_pct) },
  ]
}

resource "aws_ecs_task_definition" "daily" {
  family                   = "${local.name}-daily"
  requires_compatibilities = ["FARGATE"]
  network_mode              = "awsvpc"
  cpu                       = "1024"
  memory                    = "2048"
  execution_role_arn        = aws_iam_role.pipeline_task.arn
  task_role_arn              = aws_iam_role.pipeline_task.arn
  tags                       = local.tags

  container_definitions = jsonencode([
    {
      name        = "pipeline"
      image       = var.pipeline_image_uri
      essential   = true
      command     = ["orchestration/run_daily.sh"]
      environment = local.pipeline_environment
      secrets     = local.pipeline_secrets
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.pipeline.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "daily"
        }
      }
    }
  ])
}

resource "aws_ecs_task_definition" "hourly" {
  family                    = "${local.name}-hourly"
  requires_compatibilities  = ["FARGATE"]
  network_mode              = "awsvpc"
  cpu                       = "256"
  memory                    = "512"
  execution_role_arn        = aws_iam_role.pipeline_task.arn
  task_role_arn             = aws_iam_role.pipeline_task.arn
  tags                      = local.tags

  container_definitions = jsonencode([
    {
      name        = "pipeline"
      image       = var.pipeline_image_uri
      essential   = true
      command     = ["orchestration/run_hourly_land.sh"]
      # hourly land-only run needs only the billing API credential (Schedule:
      # "an hourly lightweight run that only lands new invoices, no transform, no publish")
      environment = local.pipeline_environment
      secrets     = [{ name = "BILLING_API_TOKEN", valueFrom = var.billing_api_token_secret_arn }]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.pipeline.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "hourly"
        }
      }
    }
  ])
}
