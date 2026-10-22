module "soap_api_gateway" {
  source = "git::https://github.com/nationalarchives/da-terraform-modules.git//apigateway?ref=main"

  api_name               = "${var.environment}-soap-api"
  environment            = var.environment
  endpoint_configuration = { types = ["REGIONAL"] }
  api_definition = jsonencode({
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

resource "aws_api_gateway_domain_name" "soap_agw_domain" {
  regional_certificate_arn = aws_acm_certificate_validation.soap_cert.certificate_arn
  endpoint_configuration {
    types = ["REGIONAL"]
  }
  domain_name = local.soap_domain_name
}

resource "aws_api_gateway_base_path_mapping" "soap_mapping" {
  api_id      = module.soap_api_gateway.rest_api.id
  stage_name  = var.environment
  domain_name = aws_api_gateway_domain_name.soap_agw_domain.domain_name
}