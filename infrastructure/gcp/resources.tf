provider "google" {
  project = var.project
  region  = var.region
}

locals {
  resource_name_prefix = "${var.name}-${var.environment}"
}

resource "google_service_account" "service_account" {
  account_id   = "${local.resource_name_prefix}-api"
  display_name = "Git LFS function service account"
}

resource "google_project_iam_binding" "role_binding" {
  role = "roles/storage.objectAdmin"

  members = [
    "serviceAccount:${google_service_account.service_account.email}"
  ]
}

resource "google_service_account_key" "key" {
  service_account_id = google_service_account.service_account.name
  public_key_type    = "TYPE_X509_PEM_FILE"
}

resource "local_file" "credentials" {
  content  = base64decode(google_service_account_key.key.private_key)
  filename = "${path.module}/credentials.json"

  provisioner "local-exec" {
    command = "zip -r ${path.module}/function_source.zip credentials.json && rm -rf credentials.json"
  }
}

resource "google_storage_bucket_object" "source_archive" {
  name   = "src/${uuid()}.zip"
  bucket = var.bucket_name
  source = "${path.module}/function_source.zip"

  depends_on = [
    local_file.credentials
  ]
}

resource "google_cloudfunctions_function" "function" {
  name                  = "${local.resource_name_prefix}-api"
  description           = "This function coordinate fetching and storing Git LFS objects"
  runtime               = "python37"
  timeout               = 30
  available_memory_mb   = 128
  source_archive_bucket = google_storage_bucket_object.source_archive.bucket
  source_archive_object = google_storage_bucket_object.source_archive.name
  trigger_http          = true
  entry_point           = "function_handler"
  ingress_settings      = "ALLOW_ALL"
  labels                = var.labels
  service_account_email = google_service_account.service_account.email
  environment_variables = {
    LOG_LEVEL                      = "INFO"
    BUCKET_NAME                    = var.bucket_name
    GOOGLE_APPLICATION_CREDENTIALS = "credentials.json"
  }
}

resource "google_cloudfunctions_function_iam_member" "invoker" {
  project        = google_cloudfunctions_function.function.project
  region         = google_cloudfunctions_function.function.region
  cloud_function = google_cloudfunctions_function.function.name

  role   = "roles/cloudfunctions.invoker"
  member = "allUsers"
}
