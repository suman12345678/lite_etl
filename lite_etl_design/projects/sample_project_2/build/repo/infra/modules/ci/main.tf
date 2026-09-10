# modules/ci - GitHub Actions OIDC provider + the per-env deploy role
# (northwind-<env>-ci) and the self-hosted runner instance profile.
# ref: deployment-and-iac.md s.4 ; requirements/08 (no stored cloud keys)
#
# Phase 4 scaffold - trust policy shape is real, account id / repo are TODO/var.

terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.60" }
  }
}

# One OIDC provider per account (create in dev; stg reuses; prd has its own).
resource "aws_iam_openid_connect_provider" "github" {
  count           = var.create_oidc_provider ? 1 : 0
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"] # TODO verify current
}

data "aws_iam_openid_connect_provider" "github" {
  count = var.create_oidc_provider ? 0 : 1
  url   = "https://token.actions.githubusercontent.com"
}

locals {
  oidc_arn = var.create_oidc_provider ? aws_iam_openid_connect_provider.github[0].arn : data.aws_iam_openid_connect_provider.github[0].arn
}

data "aws_iam_policy_document" "trust" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [local.oidc_arn]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      # only main + the matching Environment may assume the role
      values = ["repo:${var.github_repo}:ref:refs/heads/main", "repo:${var.github_repo}:environment:${var.env}"]
    }
  }
}

resource "aws_iam_role" "ci" {
  name               = "northwind-${var.env}-ci"
  assume_role_policy = data.aws_iam_policy_document.trust.json
}

# TODO least-privilege: terraform state (tfstate bucket + lock table), the
# resources each module manages, dbt on Databricks, ECS deploy for the agent.
resource "aws_iam_role_policy" "ci" {
  role   = aws_iam_role.ci.id
  policy = jsonencode({ Version = "2012-10-17", Statement = [] }) # TODO
}

resource "aws_iam_instance_profile" "runner" {
  name = "northwind-${var.env}-runner"
  role = aws_iam_role.ci.name # runners may use a narrower role - TODO split
}
