resource "aws_api_gateway_rest_api" "soap" {
  name                 = "${var.environment}-soap-api"
  security_policy      = "SecurityPolicy_TLS13_1_2_FIPS_PFS_PQ_2025_09"
  endpoint_access_mode = "BASIC"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  body = jsonencode({
    swagger = "2.0"


    info = {
      title   = "${var.environment}-soap-api"
      version = "1.0"
    }

    paths = {
      "/service.asmx" = {
        get = {
          "x-amazon-apigateway-integration" = {
            type       = "aws_proxy"
            httpMethod = "POST"
            uri        = "arn:aws:apigateway:${data.aws_region.current.region}:lambda:path/2015-03-31/functions/${aws_lambda_function.soap.arn}/invocations"
          }
        }
        post = {
          "x-amazon-apigateway-integration" = {
            type       = "aws_proxy"
            httpMethod = "POST"
            uri        = "arn:aws:apigateway:${data.aws_region.current.region}:lambda:path/2015-03-31/functions/${aws_lambda_function.soap.arn}/invocations"
          }
        }
      }
    }
  })
}

resource "aws_api_gateway_deployment" "soap" {
  rest_api_id = aws_api_gateway_rest_api.soap.id
  triggers = {
    redeployment = sha1(jsonencode(concat([aws_api_gateway_rest_api.soap.body], aws_api_gateway_rest_api.soap.endpoint_configuration, [])))
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "soap" {
  deployment_id = aws_api_gateway_deployment.soap.id
  rest_api_id   = aws_api_gateway_rest_api.soap.id
  stage_name    = var.environment

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_access_logs.arn
    format = jsonencode({
      "requestId"         = "$context.requestId",
      "extendedRequestId" = "$context.extendedRequestId",
      "ip"                = "$context.identity.sourceIp",
      "caller"            = "$context.identity.caller",
      "user"              = "$context.identity.user",
      "requestTime"       = "$context.requestTime",
      "httpMethod"        = "$context.httpMethod",
      "resourcePath"      = "$context.resourcePath",
      "status"            = "$context.status",
      "protocol"          = "$context.protocol",
      "responseLength"    = "$context.responseLength"
    })

  }
}

resource "aws_cloudwatch_log_group" "api_access_logs" {
  name              = "${var.environment}-soap-api-access-logs"
  retention_in_days = 90
}

moved {
  from = module.soap_api_gateway.aws_api_gateway_rest_api.rest_api
  to   = aws_api_gateway_rest_api.soap
}

moved {
  from = module.soap_api_gateway.aws_api_gateway_deployment.api_deployment
  to   = aws_api_gateway_deployment.soap
}

moved {
  from = module.soap_api_gateway.aws_api_gateway_stage.api_stage
  to   = aws_api_gateway_stage.soap
}

resource "aws_api_gateway_domain_name" "soap_agw_domain" {
  regional_certificate_arn = aws_acm_certificate_validation.soap_cert.certificate_arn
  security_policy          = "SecurityPolicy_TLS13_1_2_FIPS_PFS_PQ_2025_09"
  endpoint_access_mode     = "BASIC"
  endpoint_configuration {
    types = ["REGIONAL"]
  }
  domain_name = local.soap_domain_name
}

resource "aws_api_gateway_base_path_mapping" "soap_mapping" {
  api_id      = aws_api_gateway_rest_api.soap.id
  stage_name  = aws_api_gateway_stage.soap.stage_name
  domain_name = aws_api_gateway_domain_name.soap_agw_domain.domain_name
}

resource "aws_wafv2_web_acl_association" "soap_acl_association" {
  resource_arn = aws_api_gateway_stage.soap.arn
  web_acl_arn  = aws_wafv2_web_acl.api_gateway.arn
}