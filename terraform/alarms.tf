locals {
  rule_name = "${var.environment}-eventbridge-alarm-state-change-alarm-only"
}
data "aws_ssm_parameter" "slack_token" {
  name = "/${var.environment}/slack/token"
}

resource "aws_cloudwatch_event_connection" "api_connection" {
  name               = "${var.environment}-slack-connection"
  description        = "A connection for Slack"
  authorization_type = "API_KEY"

  auth_parameters {
    api_key {
      key   = "Authorization"
      value = "Bearer ${data.aws_ssm_parameter.slack_token.value}"
    }
  }
}

resource "aws_cloudwatch_event_api_destination" "api_destination" {
  name                             = "${var.environment}-eventbridge-slack-destination"
  invocation_endpoint              = "https://slack.com/api/chat.postMessage"
  http_method                      = "POST"
  invocation_rate_limit_per_second = 300
  connection_arn                   = aws_cloudwatch_event_connection.api_connection.arn
}

resource "aws_cloudwatch_event_rule" "alarm_only_rule" {
  name = local.rule_name
  event_pattern = jsonencode({
    "source" = [
      "aws.cloudwatch"
    ],
    "detail-type" = [
      "CloudWatch Alarm State Change"
    ],
    "resources" = values(aws_cloudwatch_metric_alarm.alarms_shield_ddos_detected)[*].arn
    "detail" = {
      "state" = {
        "value" = ["ALARM"]
      }
    }
  })
  event_bus_name = "default"
  state          = "ENABLED"
}

resource "aws_cloudwatch_event_target" "target" {
  target_id      = local.rule_name
  event_bus_name = "default"
  arn            = aws_cloudwatch_event_api_destination.api_destination.arn
  role_arn       = aws_iam_role.api_destination_role.arn
  rule           = aws_cloudwatch_event_rule.alarm_only_rule.name
  input_transformer {
    input_template = jsonencode(
      { "channel" = "C06EDJPF0VB", "text" : ":alert-noflash-slow: Cloudwatch alarm <alarmName> has entered state ALARM" }
    )
    input_paths = {
      "alarmName" = "$.detail.alarmName",
    }
  }
}


resource "aws_iam_role" "api_destination_role" {
  name = "${var.environment}-api-destination-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        "Sid" : "",
        "Effect" : "Allow",
        "Principal" : {
          "Service" : "events.amazonaws.com"
        },
        "Action" : "sts:AssumeRole"
      },
    ]
  })
}

resource "aws_iam_policy" "api_destination_policy" {
  name   = "${local.rule_name}-api-destination-policy"
  policy = data.aws_iam_policy_document.api_policy_document.json
}

resource "aws_iam_role_policy_attachment" "api_destination" {
  role       = aws_iam_role.api_destination_role.name
  policy_arn = aws_iam_policy.api_destination_policy.arn
}

data "aws_iam_policy_document" "api_policy_document" {
  statement {
    effect    = "Allow"
    actions   = ["events:InvokeApiDestination"]
    resources = [aws_cloudwatch_event_api_destination.api_destination.arn]
  }
}
