resource "aws_iam_role" "lambda_search_execution" {
  name = "${var.environment}-pronom-lambda-results-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role" "lambda_soap_execution" {
  name = "${var.environment}-pronom-lambda-soap-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_results" {
  role       = aws_iam_role.lambda_search_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_soap" {
  role       = aws_iam_role.lambda_soap_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "search" {
  function_name = "${var.environment}-pronom-search"
  role          = aws_iam_role.lambda_search_execution.arn
  runtime       = local.python_runtime
  handler       = "results.lambda_handler"
  filename      = "${path.module}/results.zip"
  timeout       = 60
}

resource "aws_lambda_alias" "search_alias" {
  name             = "production"
  function_name    = aws_lambda_function.search.arn
  function_version = aws_lambda_function.search.version
}

resource "aws_lambda_function" "soap" {
  function_name                  = "${var.environment}-pronom-soap-endpoint"
  role                           = aws_iam_role.lambda_soap_execution.arn
  runtime                        = local.python_runtime
  handler                        = "soap.lambda_handler"
  filename                       = "${path.module}/soap.zip"
  timeout                        = 60
  reserved_concurrent_executions = local.lambda_reserved_concurrent_executions
  source_code_hash               = filebase64sha256("${path.module}/soap.zip")
}

resource "aws_lambda_permission" "soap_api_gateway" {
  for_each      = toset(["GET", "POST"])
  statement_id  = "AllowSoapApiGatewayInvoke${title(each.value)}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.soap.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${module.soap_api_gateway.api_execution_arn}/*/${each.value}/service.asmx"
}


resource "aws_lambda_function_url" "results" {
  function_name      = aws_lambda_alias.search_alias.function_name
  qualifier          = aws_lambda_alias.search_alias.name
  authorization_type = "AWS_IAM"
}

resource "aws_iam_role" "scheduler_role" {
  name = "${var.environment}-pronom-keep-warm"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "scheduler.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "scheduler_invoke_lambda" {
  role = aws_iam_role.scheduler_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["lambda:InvokeFunction"]
      Resource = aws_lambda_function.search.arn
    }]
  })
}