resource "aws_route53_record" "a" {
  zone_id = data.aws_route53_zone.zone.zone_id
  name    = local.domain_name
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.site.domain_name
    zone_id                = aws_cloudfront_distribution.site.hosted_zone_id
    evaluate_target_health = false
  }
}

resource "aws_route53_record" "aaaa" {
  zone_id = data.aws_route53_zone.zone.zone_id
  name    = local.domain_name
  type    = "AAAA"

  alias {
    name                   = aws_cloudfront_distribution.site.domain_name
    zone_id                = aws_cloudfront_distribution.site.hosted_zone_id
    evaluate_target_health = false
  }
}

resource "aws_route53_record" "google_verification" {
  count   = var.environment == "prod" ? 1 : 0
  name    = "google-site-verification"
  records = ["vq3nRRGt1EWmwSZP9zx6ncR-dI5UO2mR-IZarh3ARxQ"]
  type    = "TXT"
  ttl     = 300
  zone_id = data.aws_route53_zone.zone.zone_id
}