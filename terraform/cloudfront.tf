locals {
  results_origin_name = "results-url-origin"
  soap_origin_name    = "soap-url-origin"
  s3_origin_name      = "s3-origin"
}
resource "aws_cloudfront_response_headers_policy" "security" {
  name    = "ResponseHeadersPolicy"
  comment = "Adds strict Content-Security-Policy for CloudFront responses"

  security_headers_config {
    content_security_policy {
      content_security_policy = local.content_security_policy
      override                = true
    }

    strict_transport_security {
      access_control_max_age_sec = 31536000
      include_subdomains         = true
      preload                    = true
      override                   = true
    }

    content_type_options {
      override = false
    }

    frame_options {
      frame_option = "DENY"
      override     = false
    }

    referrer_policy {
      referrer_policy = "strict-origin"
      override        = false
    }
  }

  custom_headers_config {
    items {
      header   = "Permissions-Policy"
      value    = local.permissions_policy_value
      override = false
    }
  }
}

resource "aws_cloudfront_origin_access_control" "s3" {
  name                              = "${var.environment}-pronom-s3-oac"
  description                       = "OAC for S3 origin"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_origin_access_control" "lambda_url" {
  name                              = "${var.environment}-pronom-results-url-oac"
  description                       = "OAC for Lambda Function URL origin"
  origin_access_control_origin_type = "lambda"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_lambda_permission" "cloudfront_invoke_results" {
  for_each      = toset(["InvokeFunction", "InvokeFunctionUrl"])
  statement_id  = "AllowCloudFront${each.value}"
  action        = "lambda:${each.value}"
  function_name = aws_lambda_function.results.function_name
  principal     = "cloudfront.amazonaws.com"
  source_arn    = aws_cloudfront_distribution.site.arn
}

resource "aws_lambda_permission" "cloudfront_invoke_soap" {
  for_each      = toset(["InvokeFunction", "InvokeFunctionUrl"])
  statement_id  = "AllowCloudFront${each.value}"
  action        = "lambda:${each.value}"
  function_name = aws_lambda_function.soap.function_name
  principal     = "cloudfront.amazonaws.com"
  source_arn    = aws_cloudfront_distribution.site.arn
}

data "aws_cloudfront_cache_policy" "caching_optimised" {
  name = "Managed-CachingOptimized"
}

data "aws_cloudfront_origin_request_policy" "all_viewer_except_host" {
  name = "Managed-AllViewerExceptHostHeader"
}

resource "aws_cloudfront_cache_policy" "cache_query_strings" {
  name        = "CacheQueryStrings"
  max_ttl     = 31536000
  min_ttl     = 1
  default_ttl = 86400
  parameters_in_cache_key_and_forwarded_to_origin {
    query_strings_config {
      query_string_behavior = "all"
    }
    cookies_config {
      cookie_behavior = "none"
    }
    headers_config {
      header_behavior = "none"
    }
  }
}

resource "aws_cloudfront_distribution" "site" {
  depends_on = [aws_acm_certificate_validation.cf]

  enabled             = true
  is_ipv6_enabled     = true
  comment             = "pronom-website"
  default_root_object = "home"
  price_class         = "PriceClass_All"
  web_acl_id          = aws_wafv2_web_acl.cloudfront.arn

  aliases = [local.domain_name]

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate.cf.arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.3_2025"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  origin {
    domain_name              = aws_s3_bucket.site.bucket_regional_domain_name
    origin_id                = local.s3_origin_name
    origin_access_control_id = aws_cloudfront_origin_access_control.s3.id
  }

  origin {
    domain_name              = replace(replace(aws_lambda_function_url.results.function_url, "https://", ""), "/", "")
    origin_id                = local.results_origin_name
    origin_access_control_id = aws_cloudfront_origin_access_control.lambda_url.id

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  origin {
    domain_name              = replace(replace(aws_lambda_function_url.soap.function_url, "https://", ""), "/", "")
    origin_id                = local.soap_origin_name
    origin_access_control_id = aws_cloudfront_origin_access_control.lambda_url.id

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    target_origin_id       = local.s3_origin_name
    viewer_protocol_policy = "redirect-to-https"

    allowed_methods = ["GET", "HEAD", "OPTIONS"]
    cached_methods  = ["GET", "HEAD", "OPTIONS"]

    cache_policy_id = data.aws_cloudfront_cache_policy.caching_optimised.id

    response_headers_policy_id = aws_cloudfront_response_headers_policy.security.id
  }

  ordered_cache_behavior {
    path_pattern           = "/results"
    target_origin_id       = local.results_origin_name
    viewer_protocol_policy = "redirect-to-https"

    allowed_methods = ["GET", "HEAD", "OPTIONS"]
    cached_methods  = ["GET", "HEAD", "OPTIONS"]

    cache_policy_id          = aws_cloudfront_cache_policy.cache_query_strings.id
    origin_request_policy_id = data.aws_cloudfront_origin_request_policy.all_viewer_except_host.id

    response_headers_policy_id = aws_cloudfront_response_headers_policy.security.id
  }

  ordered_cache_behavior {
    path_pattern           = "/service.asmx"
    target_origin_id       = local.soap_origin_name
    viewer_protocol_policy = "redirect-to-https"

    allowed_methods = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods  = ["GET", "HEAD", "OPTIONS"]

    cache_policy_id          = aws_cloudfront_cache_policy.cache_query_strings.id
    origin_request_policy_id = data.aws_cloudfront_origin_request_policy.all_viewer_except_host.id
    lambda_function_association {
      event_type   = "origin-request"
      include_body = true
      lambda_arn   = aws_lambda_function.soap_edge.qualified_arn
    }
  }

  dynamic "custom_error_response" {
    for_each = toset(local.error_response_codes)
    content {
      error_code            = custom_error_response.value
      response_code         = custom_error_response.value
      response_page_path    = "/error"
      error_caching_min_ttl = 0
    }
  }
}

resource "aws_cloudwatch_log_delivery_source" "access_logs_source" {
  name         = "${var.environment}-site-access-logs"
  log_type     = "ACCESS_LOGS"
  provider     = aws.use1
  resource_arn = aws_cloudfront_distribution.site.arn
}

resource "aws_cloudwatch_log_group" "site_access_logs" {
  name              = "${var.environment}-site-access-logs"
  provider          = aws.use1
  retention_in_days = 90
}

resource "aws_cloudwatch_log_delivery_destination" "cloudfront_logs_destination" {
  name          = "${var.environment}-site-logs-destination"
  provider      = aws.use1
  output_format = "json"
  delivery_destination_configuration {
    destination_resource_arn = aws_cloudwatch_log_group.site_access_logs.arn
  }
}

resource "aws_cloudwatch_log_delivery" "access_logs_delivery" {
  provider                 = aws.use1
  delivery_source_name     = aws_cloudwatch_log_delivery_source.access_logs_source.name
  delivery_destination_arn = aws_cloudwatch_log_delivery_destination.cloudfront_logs_destination.arn
}
