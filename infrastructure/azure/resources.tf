provider "azurerm" {
  subscription_id = var.subscription_id
  features {
  }
}

locals {
  resource_name_prefix = "${var.name}-${var.environment}"
}

resource "azurerm_resource_group" "resource_group" {
  name     = "${local.resource_name_prefix}-rg"
  location = var.location
  tags     = var.tags
}

resource "azurerm_storage_account" "storage_account" {
  name                     = replace("${local.resource_name_prefix}-sa", "-", "")
  resource_group_name      = azurerm_resource_group.resource_group.name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  tags                     = var.tags
}

resource "azurerm_storage_container" "storage_container" {
  name                  = "${var.name}-storage"
  storage_account_name  = azurerm_storage_account.storage_account.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "deployment_container" {
  name                  = "azure-webjobs-deployments"
  storage_account_name  = azurerm_storage_account.storage_account.name
  container_access_type = "private"
}

resource "azurerm_storage_blob" "function_source_code" {
  name                   = filesha256("${path.module}/function_source.zip")
  storage_account_name   = azurerm_storage_account.storage_account.name
  storage_container_name = azurerm_storage_container.deployment_container.name
  type                   = "Block"
  source                 = "${path.module}/function_source.zip"
}

data "azurerm_storage_account_sas" "storage_account_sas" {
  connection_string = azurerm_storage_account.storage_account.primary_connection_string
  https_only        = true
  start             = "2020-01-01"
  expiry            = "2022-12-31"

  resource_types {
    object    = true
    container = false
    service   = false
  }

  services {
    blob  = true
    queue = false
    table = false
    file  = false
  }

  permissions {
    read    = true
    write   = false
    delete  = false
    list    = false
    add     = false
    create  = false
    update  = false
    process = false
  }
}

resource "azurerm_app_service_plan" "service_plan" {
  name                = "${local.resource_name_prefix}-asp"
  location            = var.location
  resource_group_name = azurerm_resource_group.resource_group.name
  kind                = "Linux"
  reserved            = true
  tags                = var.tags

  sku {
    tier = "Dynamic"
    size = "Y1"
  }
}

resource "azurerm_application_insights" "application_insights" {
  name                = "${local.resource_name_prefix}-ai"
  location            = var.location
  resource_group_name = azurerm_resource_group.resource_group.name
  application_type    = "web"
}

resource "azurerm_function_app" "function_app" {
  name                       = "${local.resource_name_prefix}-fn"
  location                   = var.location
  resource_group_name        = azurerm_resource_group.resource_group.name
  app_service_plan_id        = azurerm_app_service_plan.service_plan.id
  storage_account_name       = azurerm_storage_account.storage_account.name
  storage_account_access_key = azurerm_storage_account.storage_account.primary_access_key
  https_only                 = true
  version                    = "~3"
  tags                       = var.tags

  app_settings = {
    FUNCTIONS_WORKER_RUNTIME       = "python"
    FUNCTIONS_EXTENSION_VERSION    = "~3"
    APPINSIGHTS_INSTRUMENTATIONKEY = azurerm_application_insights.application_insights.instrumentation_key
    WEBSITE_RUN_FROM_PACKAGE       = "${azurerm_storage_blob.function_source_code.url}${data.azurerm_storage_account_sas.storage_account_sas.sas}"
    STORAGE_ACCOUNT                = azurerm_storage_account.storage_account.name
    STORAGE_ACCOUNT_PRIMARY_KEY    = azurerm_storage_account.storage_account.primary_access_key
    STORAGE_CONTAINER              = azurerm_storage_container.storage_container.name
    LOG_LEVEL                      = "INFO"
  }

  site_config {
    linux_fx_version = "python|3.7"
  }
}
