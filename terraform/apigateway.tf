resource "aws_api_gateway_rest_api" "soap" {
  name = "${var.environment}-soap-api"

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