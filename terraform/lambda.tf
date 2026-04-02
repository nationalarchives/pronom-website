resource "aws_iam_role" "lambda_results_execution" {
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

resource "aws_iam_role" "edge_lambda_execution" {
  name = "${var.environment}-pronom-edge-lambda-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = ["lambda.amazonaws.com", "edgelambda.amazonaws.com"] }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "edge_lambda_basic" {
  role       = aws_iam_role.edge_lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_results" {
  role       = aws_iam_role.lambda_results_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_soap" {
  role       = aws_iam_role.lambda_soap_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "results" {
  function_name = "${var.environment}-pronom-search"
  role          = aws_iam_role.lambda_results_execution.arn
  runtime       = local.python_runtime
  handler       = "results.lambda_handler"
  filename      = "${path.module}/results.zip"
  timeout       = 60
  snap_start {
    apply_on = "PublishedVersions"
  }
  publish                        = true
  reserved_concurrent_executions = local.lambda_reserved_concurrent_executions
  source_code_hash               = filebase64sha256("${path.module}/results.zip")
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

data "archive_file" "edge_lambda_code" {
  type        = "zip"
  source_file = "${path.module}/lambda/index.mjs"
  output_path = "${path.module}/lambda/edge_function.zip"
}

resource "aws_lambda_function" "soap_edge" {
  function_name                  = "${var.environment}-pronom-soap-edge"
  role                           = aws_iam_role.edge_lambda_execution.arn
  runtime                        = "nodejs22.x"
  handler                        = "index.handler"
  filename                       = data.archive_file.edge_lambda_code.output_path
  source_code_hash               = data.archive_file.edge_lambda_code.output_base64sha256
  provider                       = aws.use1
  publish                        = true
  reserved_concurrent_executions = local.lambda_reserved_concurrent_executions
}

resource "aws_lambda_function_url" "results" {
  function_name      = aws_lambda_function.results.function_name
  authorization_type = "AWS_IAM"
}

resource "aws_lambda_function_url" "soap" {
  function_name      = aws_lambda_function.soap.function_name
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
      Resource = aws_lambda_function.results.arn
    }]
  })
}

resource "aws_scheduler_schedule" "keep_warm" {
  name       = "${var.environment}-pronom-keep-warm-schedule"
  group_name = "default"

  flexible_time_window { mode = "OFF" }
  schedule_expression = "rate(5 minutes)"

  target {
    arn      = aws_lambda_function.results.arn
    role_arn = aws_iam_role.scheduler_role.arn
    input    = jsonencode({})
  }
}