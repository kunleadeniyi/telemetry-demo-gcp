provider "google" {
  credentials = file("../credentials.json")
#   project = "idyllic-web-401116"
  project = var.project_id
  region = "europe-west2"
}

# Google cloud storage
resource "google_storage_bucket" "storage-bucket" {
  name = var.storage_bucket
  location = var.location
}

# terraform backend
#terraform {
#  backend "gcs" {
#    bucket = "gcp-demo-telemetry-terraform-backend"
#    prefix  = "terraform/state"
#  }
#}

# pub sub
resource "google_pubsub_topic" "valid-data-topic" {
  name = var.valid_data_topic
#  message_retention_duration = "86400s"
}

resource "google_pubsub_topic" "invalid-data-topic" {
  name = var.invalid_data_topic
}

# Subscriptions for valid topic pub sub
resource "google_pubsub_subscription" "valid-data-sub" {
  name = var.valid_data_topic_default_subscription
  topic = google_pubsub_topic.valid-data-topic.name
  message_retention_duration = var.subscription_message_retention
}

# Subscriptions for valid topic pub sub
resource "google_pubsub_subscription" "dataflow-valid-data-sub" {
  name = var.valid_data_topic_subscription_for_dataflow
  topic = google_pubsub_topic.valid-data-topic.name
  message_retention_duration = var.subscription_message_retention
}

# Subscriptions for invalid topic pub sub
resource "google_pubsub_subscription" "default-invalid-data-sub" {
  name = var.invalid_data_topic_default_subscription
  topic = google_pubsub_topic.invalid-data-topic.name
}

resource "google_bigquery_dataset" "gbq-dataset" {
  # name only allows underscore
  dataset_id = var.valid_bigquery_dataset
  location = var.location
   delete_contents_on_destroy = true
}

# BigQuery Provision for invalid data
# https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/pubsub_subscription#example-usage---pubsub-subscription-push-bq
resource "google_bigquery_dataset" "gbq-invalid-dataset" {
  dataset_id = var.invalid_bigquery_dataset
  location = var.location
  delete_contents_on_destroy = true
}

resource "google_bigquery_table" "gbq-invalid-dataset-error-table" {
  dataset_id = google_bigquery_dataset.gbq-invalid-dataset.dataset_id
  table_id = "errors"
  deletion_protection = false

  schema = <<EOF
  [
      {
          "name": "data",
          "type": "STRING"
      },
      {
          "name": "error",
          "type": "STRING"
      },
      {
          "name": "timestamp",
          "type": "STRING"
      }
  ]
  EOF
}

data "google_project" "project" {
}

resource "google_project_iam_member" "viewer" {
  project = data.google_project.project.project_id
  role   = "roles/bigquery.metadataViewer"
  member = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

resource "google_project_iam_member" "editor" {
  project = data.google_project.project.project_id
  role   = "roles/bigquery.dataEditor"
  member = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

# pubsub push to bigquery
resource "google_pubsub_subscription" "push-invalid-data-to-bq" {
  name = "push-invalid-data-to-bq"
  topic = google_pubsub_topic.invalid-data-topic.name

  bigquery_config {
    table = "${data.google_project.project.project_id}.${google_bigquery_table.gbq-invalid-dataset-error-table.dataset_id}.${google_bigquery_table.gbq-invalid-dataset-error-table.table_id}"
  }

  depends_on = [google_project_iam_member.viewer, google_project_iam_member.editor]
}

# notification channel
resource "google_monitoring_notification_channel" "emails" {
  for_each = { for email_details in var.emails : email_details.email => email_details }

  type = each.value.type
  display_name = each.value.display_name

  labels = {
    email_address = each.value.email
  }
  force_delete = true
}

# create artifact registry repository to store container
resource "google_artifact_registry_repository" "cloud-run-api-repo" {
  location      = var.location
  repository_id = var.cloud_run_api_repo.id
  description   = var.cloud_run_api_repo.description
  format        = var.cloud_run_api_repo.format
}

# artifact registry iam
resource "google_project_iam_member" "artifact-registry-admin" {
  project = data.google_project.project.project_id
  role   = "roles/artifactregistry.admin"
  member = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}


# # Google Big Query Table (depends on GBQ dataset)
# # valid table
# resource "google_bigquery_table" "demo-gbq-dataset-valid-table" {
#   dataset_id = google_bigquery_dataset.demo-gbq-dataset.dataset_id
#   table_id = "demo-gbq-dataset-valid-table"
#   deletion_protection = false # so I can delete with terraform destroy even when things are in it
# }

# # invalid table
# resource "google_bigquery_table" "demo-gbq-dataset-invalid-table" {
#   dataset_id = google_bigquery_dataset.demo-gbq-dataset.dataset_id
#   table_id = "demo-gbq-dataset-invalid-table"
#   deletion_protection = false
# }

# # connect pub-sub to big query using dataflow
# # Create Google Cloud Dataflow job
# resource "google_dataflow_job" "demo-dataflow-job" {
#     name = "demo-dataflow-job-to-gcp"
#     temp_gcs_location = "gs://${google_storage_bucket.demo-storage-bucket.name}/dataflow_temp"
#     # template_gcs_path = "gs://${google_storage_bucket.demo-storage-bucket.name}/templates/dataflow_template"
#     template_gcs_path = "gs://dataflow-templates-europe-west2/latest/PubSub_Subscription_to_BigQuery"
#     on_delete  = "cancel"
#     enable_streaming_engine = true

#     parameters = {
#         # inputTopic = google_pubsub_topic.demo-valid-data.name # Input Pub/Sub topic
#         # inputSubscription: "projects/PROJECT_ID/subscriptions/SUBSCRIPTION_NAME"
#         # outputTableSpec: "PROJECT_ID:DATASET.TABLE_NAME"

#         inputSubscription = "projects/idyllic-web-401116/subscriptions/${google_pubsub_subscription.demo-valid-data-sub.name}"
#         outputTableSpec = "idyllic-web-401116:${google_bigquery_dataset.demo-gbq-dataset.dataset_id}.${google_bigquery_table.demo-gbq-dataset-valid-table.table_id}" # "<YOUR_PROJECT_ID>:<YOUR_DATASET_ID>.<YOUR_TABLE_ID>" # Output BigQuery table
#     }
# }