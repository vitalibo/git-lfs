variable "project" {
  type        = string
  description = "The default project to manage resources in"
}

variable "region" {
  type        = string
  description = "The Google Cloud region to use"
}

variable "environment" {
  type        = string
  description = "Environment name"
}

variable "name" {
  type        = string
  description = "Service name that will be prefixed to resource names"
}

variable "bucket_name" {
  type        = string
  description = "Google Storage bucket name where will be stored Git LFS objects"
}

variable "labels" {
  type        = map(string)
  description = "A list of labels to apply to resources"
}
