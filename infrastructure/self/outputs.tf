output "endpoint" {
  description = "The endpoint of the Git LFS server"
  value       = "http://${var.endpoint}:${var.port}/"
}
