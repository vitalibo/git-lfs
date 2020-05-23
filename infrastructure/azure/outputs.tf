output "resource_group" {
  description = "The name of the resource group"
  value       = azurerm_resource_group.resource_group.name
}

output "storage_account_name" {
  description = "The name of the storage account"
  value       = azurerm_storage_account.storage_account.name
}

output "storage_account_primary_access_key" {
  description = "The primary access key for the storage account"
  value       = azurerm_storage_account.storage_account.primary_access_key
}

output "service_plan" {
  description = "The name of the App Service Plan component"
  value       = azurerm_app_service_plan.service_plan.name
}

output "application_insights" {
  description = "The name of the Application Insights component"
  value       = azurerm_application_insights.application_insights.name
}

output "function_app_name" {
  description = "The name of the Function App"
  value       = azurerm_function_app.function_app.name
}

output "function_app_endpoint" {
  description = "The endpoint of the Function App"
  value       = "https://${azurerm_function_app.function_app.default_hostname}/api/"
}
