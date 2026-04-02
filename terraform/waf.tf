resource "aws_wafv2_web_acl" "cloudfront" {
  provider = aws.use1
  name     = "${var.environment}-wafwebacl-pronom-website"
  scope    = "CLOUDFRONT"

  default_action {
    allow {}
  }

  rule {
    name     = "RateLimit"
    priority = 1

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = local.waf_rate_limit
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimit"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "pronomWebsite"
    sampled_requests_enabled   = true
  }
}

resource "aws_cloudwatch_log_group" "waf_log_group" {
  provider          = aws.use1
  name              = "aws-waf-logs-pronom-site"
  retention_in_days = 90
}

resource "aws_wafv2_web_acl_logging_configuration" "cloudwatch_log_config" {
  provider                = aws.use1
  log_destination_configs = [aws_cloudwatch_log_group.waf_log_group.arn]
  resource_arn            = aws_wafv2_web_acl.cloudfront.arn
}

resource "aws_cloudwatch_log_resource_policy" "cloudwatch_log_policy" {
  provider        = aws.use1
  policy_document = data.aws_iam_policy_document.example.json
  policy_name     = "${var.environment}-cloudwatch-log-policy"
}

data "aws_iam_policy_document" "example" {
  version = "2012-10-17"
  statement {
    effect = "Allow"
    principals {
      identifiers = ["delivery.logs.amazonaws.com"]
      type        = "Service"
    }
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${aws_cloudwatch_log_group.waf_log_group.arn}:*"]
    condition {
      test     = "ArnLike"
      values   = ["arn:aws:logs:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:*"]
      variable = "aws:SourceArn"
    }
    condition {
      test     = "StringEquals"
      values   = [tostring(data.aws_caller_identity.current.account_id)]
      variable = "aws:SourceAccount"
    }
  }
}

data "aws_region" "current" {}

data "aws_caller_identity" "current" {}