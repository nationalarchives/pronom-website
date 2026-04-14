locals {
  hosted_zone_arn = "arn:aws:route53:::hostedzone/${var.hosted_zone_id}"
}
resource "aws_shield_subscription" "subscription" {
  auto_renew = "ENABLED"
}

resource "aws_shield_protection" "route53_shield_protection" {
  name         = "${local.domain_name}."
  resource_arn = local.hosted_zone_arn
}

resource "aws_shield_protection" "cloudfront_shield_protection" {
  name         = "${var.environment}-cloudfront-shield-protection"
  resource_arn = aws_cloudfront_distribution.site.arn
}

resource "aws_iam_role" "shield_drt" {
  name = "${var.environment}-shield-drt-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        "Sid" : "",
        "Effect" : "Allow",
        "Principal" : {
          "Service" : "drt.shield.amazonaws.com"
        },
        "Action" : "sts:AssumeRole"
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "shield_drt" {
  role       = aws_iam_role.shield_drt.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSShieldDRTAccessPolicy"
}

resource "aws_shield_drt_access_role_arn_association" "shield_drt" {
  role_arn = aws_iam_role.shield_drt.arn
}

resource "aws_cloudwatch_metric_alarm" "alarms_shield_ddos_detected" {
  for_each          = toset([local.hosted_zone_arn, aws_cloudfront_distribution.site.arn])
  alarm_description = "Indicates a DDoS event for a specific Amazon Resource Name (ARN)"
  alarm_name        = format("AWS/DDoSProtection DDoSDetected on Environment=%s, LB=%s", var.environment, each.key)

  metric_query {
    account_id  = data.aws_caller_identity.current.id
    id          = "m1"
    return_data = "true"

    metric {
      metric_name = "DDoSDetected"
      namespace   = "AWS/DDoSProtection"
      stat        = "Sum"
      period      = 60
      dimensions = {
        ResourceArn = each.key
      }
    }
  }
  evaluation_periods  = 20
  datapoints_to_alarm = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
}

