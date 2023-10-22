provider "google" {
  credentials = "${file("credentials.json")}"
  project = "idyllic-web-401116"
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

# Subsrciptions for pub sub
resource "google_pubsub_subscription" "demo-valid-data-sub" {
  name = "demo-valid-data-sub"
  topic = google_pubsub_topic.demo-valid-data.name
}

# Subsrciptions for pub sub
resource "google_pubsub_subscription" "demo-default-valid-data-sub" {
  name = "demo-default-valid-data-sub"
  topic = google_pubsub_topic.demo-valid-data.name
}

# Google cloud storage
resource "google_storage_bucket" "demo-storage-bucket" {
  name = "demo-storage-bucket-401116"
  location = "europe-west2"
}

resource "google_bigquery_dataset" "demo-gbq-dataset" {
  # name only allows underscore
  dataset_id = "demo_gbq_dataset"
  delete_contents_on_destroy = true
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