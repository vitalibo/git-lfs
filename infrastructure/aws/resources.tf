provider "aws" {
  profile = var.profile
  region  = var.region
}

locals {
  resource_name_prefix = "${var.name}-${var.environment}"
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
      "s3:*"
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
