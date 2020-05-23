variable "subscription_id" {
  type        = string
  description = "The Subscription ID which should be used"
}

variable "location" {
  type        = string
  description = "The Azure Region where the Resource Group should exist"
}

variable "environment" {
  type        = string
  description = "Environment name"
}

variable "name" {
  type        = string
  description = "Service name that will be prefixed to resource names"
}

variable "tags" {
  type        = map(string)
  description = "A list of tags to apply to resources"
}
