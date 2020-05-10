provider "aws" {
  profile = var.profile
  region  = var.region
}

data "aws_caller_identity" "iam" {
}

locals {
  resource_name_prefix = "${var.name}-${var.environment}"
  account_id           = data.aws_caller_identity.iam.account_id
}

data "local_file" "lambda_source" {
  filename = "${path.module}/function_source.zip"
}

resource "aws_lambda_function" "lambda" {
  function_name    = "${local.resource_name_prefix}-api"
  description      = "This lambda coordinate fetching and storing Git LFS objects"
  filename         = data.local_file.lambda_source.filename
  source_code_hash = filebase64sha256(data.local_file.lambda_source.filename)
  role             = aws_iam_role.lambda_role.arn
  handler          = "aws.function.handler"
  runtime          = "python3.7"
  memory_size      = 128
  timeout          = 30
  tags             = var.tags

  environment {
    variables = {
      LOG_LEVEL = "DEBUG"
    }
  }
}

data "aws_iam_policy_document" "lambda_role_trust_policy" {
  version = "2012-10-17"

  statement {
    actions = ["sts:AssumeRole"]
    effect  = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_role" {
  name               = "${local.resource_name_prefix}-api-lambda"
  assume_role_policy = data.aws_iam_policy_document.lambda_role_trust_policy.json
  tags               = var.tags
}

data "aws_iam_policy_document" "lambda_role_policy" {
  version = "2012-10-17"

  statement {
    effect = "Allow"

    actions = [
      "s3:GetObject*",
      "s3:PutObject*"
    ]

    resources = [
      "arn:aws:s3:::${var.bucket_name}",
      "arn:aws:s3:::${var.bucket_name}/*"
    ]
  }

  statement {
    effect = "Allow"

    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]

    resources = [
      aws_cloudwatch_log_group.lambda_log_group.arn
    ]
  }
}

resource "aws_iam_role_policy" "lambda_role_policy" {
  name_prefix = local.resource_name_prefix
  role        = aws_iam_role.lambda_role.id
  policy      = data.aws_iam_policy_document.lambda_role_policy.json
}

resource "aws_cloudwatch_log_group" "lambda_log_group" {
  name              = "/aws/lambda/${local.resource_name_prefix}-api"
  retention_in_days = 7
  tags              = var.tags
}

resource "aws_api_gateway_rest_api" "apigw" {
  name        = "${local.resource_name_prefix}-api"
  description = "Git LFS serverless RESTful API"
}

resource "aws_api_gateway_deployment" "apigw_deployment" {
  rest_api_id = aws_api_gateway_rest_api.apigw.id
  stage_name  = var.environment

  depends_on = [
    aws_api_gateway_integration.apigw_request_method_integration,
    aws_api_gateway_integration_response.apigw_response_method_integration
  ]
}

resource "aws_api_gateway_resource" "apigw_proxy" {
  rest_api_id = aws_api_gateway_rest_api.apigw.id
  parent_id   = aws_api_gateway_rest_api.apigw.root_resource_id
  path_part   = "{proxy+}"
}

resource "aws_api_gateway_method" "apigw_request_method" {
  rest_api_id   = aws_api_gateway_rest_api.apigw.id
  resource_id   = aws_api_gateway_resource.apigw_proxy.id
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "apigw_request_method_integration" {
  rest_api_id             = aws_api_gateway_rest_api.apigw.id
  resource_id             = aws_api_gateway_resource.apigw_proxy.id
  http_method             = aws_api_gateway_method.apigw_request_method.http_method
  type                    = "AWS_PROXY"
  uri                     = "arn:aws:apigateway:${var.region}:lambda:path/2015-03-31/functions/${aws_lambda_function.lambda.arn}/invocations"
  integration_http_method = "POST"
}

resource "aws_api_gateway_method_response" "apigw_response_method" {
  rest_api_id = aws_api_gateway_rest_api.apigw.id
  resource_id = aws_api_gateway_resource.apigw_proxy.id
  http_method = aws_api_gateway_integration.apigw_request_method_integration.http_method
  status_code = "200"

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "apigw_response_method_integration" {
  rest_api_id = aws_api_gateway_rest_api.apigw.id
  resource_id = aws_api_gateway_resource.apigw_proxy.id
  http_method = aws_api_gateway_method_response.apigw_response_method.http_method
  status_code = aws_api_gateway_method_response.apigw_response_method.status_code

  response_templates = {
    "application/json" = ""
  }
}

resource "aws_lambda_permission" "lambda_apigw_permission" {
  function_name = aws_lambda_function.lambda.function_name
  action        = "lambda:InvokeFunction"
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${var.region}:${local.account_id}:${aws_api_gateway_rest_api.apigw.id}/*/*${aws_api_gateway_resource.apigw_proxy.path}"

  depends_on = [
    aws_api_gateway_rest_api.apigw,
    aws_api_gateway_resource.apigw_proxy
  ]
}
