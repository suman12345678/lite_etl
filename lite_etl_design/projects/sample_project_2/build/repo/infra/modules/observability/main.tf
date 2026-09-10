# modules/observability - CloudWatch alarms + SNS -> PagerDuty / Slack for the
# alert points in pipeline-blueprint.md. ref: requirements/09
#
# Phase 4 scaffold - alarm shapes named; thresholds / ARNs are var refs / TODO.

terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.60" }
  }
}

resource "aws_sns_topic" "alerts" {
  name = "northwind-${var.env}-alerts"
}

# PagerDuty via https subscription; Slack via AWS Chatbot (configured out-of-band).
resource "aws_sns_topic_subscription" "pagerduty" {
  count     = var.pagerduty_endpoint == "" ? 0 : 1
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "https"
  endpoint  = var.pagerduty_endpoint # TODO from Secrets Manager, not literal
}

# --- alarms (pipeline-blueprint.md "Alert points") ---------------------------
resource "aws_cloudwatch_metric_alarm" "cost_budget" {
  alarm_name          = "northwind-${var.env}-cost-80pct"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  threshold           = var.monthly_budget_usd * 0.8 # TODO
  namespace           = "AWS/Billing"                # TODO or a custom cost metric
  metric_name         = "EstimatedCharges"
  period              = 21600
  statistic           = "Maximum"
  alarm_actions       = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "source_freshness" {
  alarm_name          = "northwind-${var.env}-source-freshness"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  threshold           = 1 # >=1 stale source
  namespace           = "Northwind/Pipeline"
  metric_name         = "StaleSources" # emitted by obs.metrics
  period              = 3600
  statistic           = "Maximum"
  alarm_actions       = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "sla_0600" {
  alarm_name          = "northwind-${var.env}-publish-sla-0600"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  threshold           = 1 # _SUCCESS count for today's D
  namespace           = "Northwind/Pipeline"
  metric_name         = "PublishSuccess"
  period              = 300
  statistic           = "Maximum"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  # evaluated just after 06:00 UTC - TODO: metric-math / scheduled query
}

resource "aws_cloudwatch_dashboard" "pipeline" {
  dashboard_name = "northwind-${var.env}-pipeline"
  dashboard_body = jsonencode({ widgets = [] }) # TODO freshness / build time / recon / cost widgets
}
