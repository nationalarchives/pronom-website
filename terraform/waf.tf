resource "aws_wafv2_web_acl" "cloudfront" {
  region = local.us_east_1
  name   = "${var.environment}-wafwebacl-pronom-website"
  scope  = "CLOUDFRONT"

  default_action {
    allow {}
  }

  rule {
    name     = "AntiDDOS"
    priority = 3

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesAntiDDoSRuleSet"
        vendor_name = "AWS"

        managed_rule_group_configs {
          aws_managed_rules_anti_ddos_rule_set {
            client_side_action_config {
              challenge {
                usage_of_action = "DISABLED"
              }
            }
          }
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AntiDDOS"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "HumanRateLimit"
    priority = 2

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = local.human_rate_limit
        aggregate_key_type = "IP"
        scope_down_statement {
          and_statement {
            statement {
              not_statement {
                statement {
                  byte_match_statement {
                    field_to_match {
                      uri_path {}
                    }
                    positional_constraint = "ENDS_WITH"
                    search_string         = ".xml"
                    text_transformation {
                      priority = 0
                      type     = "NONE"
                    }
                  }
                }
              }
            }
            statement {
              not_statement {
                statement {
                  byte_match_statement {
                    field_to_match {
                      uri_path {}
                    }
                    positional_constraint = "ENDS_WITH"
                    search_string         = ".json"
                    text_transformation {
                      priority = 0
                      type     = "NONE"
                    }
                  }
                }
              }
            }
          }
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "HumanRateLimit"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "MachineRateLimit"
    priority = 1

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = local.machine_rate_limit
        aggregate_key_type = "IP"
        scope_down_statement {
          or_statement {
            statement {
              byte_match_statement {
                field_to_match {
                  uri_path {}
                }
                positional_constraint = "ENDS_WITH"
                search_string         = ".xml"
                text_transformation {
                  priority = 0
                  type     = "NONE"
                }
              }
            }
            statement {
              byte_match_statement {
                field_to_match {
                  uri_path {}
                }
                positional_constraint = "ENDS_WITH"
                search_string         = ".json"
                text_transformation {
                  priority = 0
                  type     = "NONE"
                }
              }
            }
          }
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "MachineRateLimit"
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
  region            = local.us_east_1
  name              = "aws-waf-logs-${var.environment}-pronom-site"
  retention_in_days = 90
}

resource "aws_wafv2_web_acl_logging_configuration" "cloudwatch_log_config" {
  region                  = local.us_east_1
  log_destination_configs = [aws_cloudwatch_log_group.waf_log_group.arn]
  resource_arn            = aws_wafv2_web_acl.cloudfront.arn
}

resource "aws_cloudwatch_log_resource_policy" "cloudwatch_log_policy" {
  region          = local.us_east_1
  policy_document = data.aws_iam_policy_document.cloudwatch_log_policy_document.json
  policy_name     = "${var.environment}-cloudwatch-log-policy"
}

data "aws_iam_policy_document" "cloudwatch_log_policy_document" {
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
      test = "ArnLike"
      values = [
        "arn:aws:logs:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:*",
        "arn:aws:logs:${local.us_east_1}:${data.aws_caller_identity.current.account_id}:*",
      ]
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