variable "name" {
  type        = string
  description = "Service name that will be prefixed to resource names"
}

variable "environment" {
  type        = string
  description = "Environment name"
}

variable "volume" {
  type        = string
  description = "Volume path where will be stored Git LFS objects"
}

variable "port" {
  type        = number
  description = "Port of the web server"
}

variable "endpoint" {
  type        = string
  description = "Public endpoint address"
}

variable "protocol" {
  type        = string
  description = "Protocol used for the web server"
}
