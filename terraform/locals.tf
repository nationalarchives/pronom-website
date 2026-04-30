locals {
  bucket_name = "${var.environment}-pronom-site"

  permissions_policy_value = "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()"

  waf_rate_limit = 100

  error_response_codes = [403, 404, 500, 502, 503, 504]

  domain_name = "pronom.nationalarchives.gov.uk"

  allowed_style_shas = [
    "sha256-47DEQpj8HBSa+/TImW+5JCeuQeRkm5NMpJWZG3hSuFU=", # This is the sha of the empty string which any Chromium browser tries to load when rendering XML files
    "sha256-p08VBe6m5i8+qtXWjnH/AN3klt1l4uoOLsjNn8BjdQo="  # This is the sha of the inline stylesheet which Chromium browsers use to render XML files. This seems to be static.
  ]

  content_security_policy = "default-src 'self'; base-uri 'none'; object-src 'none'; font-src 'self' https://fonts.gstatic.com https://use.typekit.net; style-src 'self' https://www.nationalarchives.gov.uk https://fonts.googleapis.com https://p.typekit.net https://use.typekit.net '${join("' '", local.allowed_style_shas)}'; script-src 'self' https://www.nationalarchives.gov.uk"

  python_runtime = "python3.13"

  lambda_reserved_concurrent_executions = 100

  us_east_1 = "us-east-1"
}