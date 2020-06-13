provider "docker" {
}

locals {
  resource_name_prefix = "${var.name}-${var.environment}"
}

resource "null_resource" "image_build" {
  triggers = {
    build_number = timestamp()
  }

  provisioner "local-exec" {
    command     = "docker build -t ${local.resource_name_prefix} ."
    interpreter = [
      "bash",
      "-c"
    ]
  }
}
resource "docker_image" "image" {
  depends_on = [
    null_resource.image_build
  ]

  name = local.resource_name_prefix
}

resource "docker_container" "container" {
  image = docker_image.image.latest
  name  = local.resource_name_prefix
  ports {
    internal = 5000
    external = var.port
  }

  env = [
    "ENDPOINT=${var.protocol}://${var.endpoint}:${var.port}/"
  ]

  volumes {
    container_path = "/data"
    host_path      = var.volume
  }
}
