module "soap_api_gateway" {
  source = "git::https://github.com/nationalarchives/da-terraform-modules.git//apigateway"

  api_name    = "${var.environment}-soap-api"
  environment = var.environment

  api_definition = jsonencode({
    swagger = "2.0"


    info = {
      title   = "${var.environment}--soap-api"
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