output "function_name" {
  description = "The name of the Lambda function"
  value       = aws_lambda_function.lambda.function_name
}

output "function_arn" {
  description = "The ARN of the Lambda function"
  value       = aws_lambda_function.lambda.arn
}

output "role_name" {
  description = "The name of the IAM role created for the Lambda function"
  value       = aws_iam_role.lambda_role.name
}

output "role_arn" {
  description = "The ARN of the IAM role created for the Lambda function"
  value       = aws_iam_role.lambda_role.arn
}

output "api_gateway_id" {
  description = "The API Gateway REST id"
  value       = aws_api_gateway_rest_api.apigw.id
}

output "api_gateway_endpoint" {
  description = "The API Gateway enpoint URL address"
  value       = aws_api_gateway_deployment.apigw_deployment.invoke_url
}
