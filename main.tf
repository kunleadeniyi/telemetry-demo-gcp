provider "google" {
  credentials = "${file("credentials.json")}"
#   project = "idyllic-web-401116"
  project = "gcp-demo-telemetry"
  region = "europe-west2"
}

# resource "google_compute_instance" "demo-instance" {
#   name = "terraform-instance"
#   machine_type = "f1-micro"
#   zone = "europe-west2-a"
#   allow_stopping_for_update = true

#   boot_disk {
#     initialize_params {
#       image = "ubuntu-os-cloud/ubuntu-2004-lts"
#     }
#   }

#   network_interface {
#     network = "default"
#     access_config {
#       // necessary even if empty
#     }
#   }
# }

# Cloud run
# resource "google_cloud_run_service" "demo-cloud-run-service" {
#   name = "demo-cloud-run-service"
#   location = "europe-west2"
#   template {
#     spec {
#       containers {
#         image = "node:latest"
#       }
#     }
#   }
# }

# pub sub
resource "google_pubsub_topic" "demo-valid-data" {
  name = "demo-valid-data"
  message_retention_duration = "86400s"
}

resource "google_pubsub_topic" "demo-invalid-data" {
  name = "demo-invalid-data"
}

# Subscriptions for valid topic pub sub
resource "google_pubsub_subscription" "demo-valid-data-sub" {
  name = "demo-valid-data-sub"
  topic = google_pubsub_topic.demo-valid-data.name
}

# Subscriptions for valid topic pub sub
resource "google_pubsub_subscription" "demo-default-valid-data-sub" {
  name = "demo-default-valid-data-sub"
  topic = google_pubsub_topic.demo-valid-data.name
}

# Subscriptions for invalid topic pub sub
resource "google_pubsub_subscription" "demo-default-invalid-data-sub" {
  name = "demo-default-invalid-data-sub"
  topic = google_pubsub_topic.demo-invalid-data.name
}

# Google cloud storage
resource "google_storage_bucket" "demo-storage-bucket" {
#   name = "demo-storage-bucket-401116"
  name = "demo-gcp-telemetry-storage-bucket"
  location = "europe-west2"
}

resource "google_bigquery_dataset" "demo-gbq-dataset" {
  # name only allows underscore
  dataset_id = "demo_gbq_dataset"
  # delete_contents_on_destroy = true
}

# BigQuery Provision for invalid data
# https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/pubsub_subscription#example-usage---pubsub-subscription-push-bq
resource "google_bigquery_dataset" "demo-gbq-invalid-dataset" {
  dataset_id = "demo_gbq_invalid_dataset"
}

resource "google_bigquery_table" "demo-gbq-invalid-dataset-error-table" {
  dataset_id = google_bigquery_dataset.demo-gbq-invalid-dataset.dataset_id
  table_id = "errors"

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
resource "google_pubsub_subscription" "demo-push-invalid-data-to-bq" {
  name = "demo-push-invalid-data-to-bq"
  topic = google_pubsub_topic.demo-invalid-data.name

  bigquery_config {
    table = "${data.google_project.project.project_id}.${google_bigquery_table.demo-gbq-invalid-dataset-error-table.dataset_id}.${google_bigquery_table.demo-gbq-invalid-dataset-error-table.table_id}"
  }

  depends_on = [google_project_iam_member.viewer, google_project_iam_member.editor]
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