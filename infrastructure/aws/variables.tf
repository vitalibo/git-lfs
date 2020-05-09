variable "profile" {
  type        = string
  description = "Use a specific profile from your credential file"
  default     = "default"
}

variable "region" {
  type        = string
  description = "The AWS region to use"
  default     = "us-west-2"
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
  description = "S3 bucket name where will be stored Git LFS objects"
}

variable "tags" {
  type        = map(string)
  description = "A list of tags to apply to resources"
}
