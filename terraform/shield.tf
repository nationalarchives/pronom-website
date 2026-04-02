resource "aws_shield_subscription" "subscription" {
  auto_renew = "ENABLED"
}

resource "aws_shield_protection" "route53_shield_protection" {
  name         = "${local.domain_name}."
  resource_arn = "arn:aws:route53:::hostedzone/Z0207922GVVLB5378323"
}

resource "aws_shield_protection" "cloudfront_shield_protection" {
  name         = "${var.environment}-cloudfront-shield-protection"
  resource_arn = aws_cloudfront_distribution.site.arn
}

resource "aws_iam_role" "shield_drt" {
  name = "example-role"
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