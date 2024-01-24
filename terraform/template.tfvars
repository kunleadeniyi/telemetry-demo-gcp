project_id = ""
valid_data_topic = ""
invalid_data_topic = ""
valid_data_topic_default_subscription = ""
invalid_data_topic_default_subscription = ""
valid_data_topic_subscription_for_dataflow = ""
subscription_message_retention = "86400s" # 1 day
storage_bucket = "" # Use only lower-case letters, numbers, hyphens (-) and underscores (_). Dots (.) may be used to form a valid domain name. (globally unique)
valid_bigquery_dataset = ""
invalid_bigquery_dataset = ""
invalid_bigquery_dataset_error_table_id = ""

emails = [
  {
    email=""
    display_name=""
    type="email"
  },
  {
    email=""
    display_name=""
    type="email"
  }
]

cloud_run_api_repo = {
  id = "" # Names may only contain lowercase letters, numbers and hyphens
  description = "sample gcr repository from cloud run container images"
  format = "DOCKER"
}

cloud_run_service = {
  name = ""
  cpu = ""
  memory = ""
}

cloud_run_container_image = "[ARTIFACT_REGISTRY_LOCATION]-docker.pkg.dev/[PROJECT_ID]/[REPO_NAME]/[IMAGE]"

# load balancer
ssl = false
domain = null