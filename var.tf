variable "project_id" {
  type = string
}

variable "location" {
  type = string
  default = "europe-west2"
}

variable "valid_data_topic" {
  type = string
}

variable "invalid_data_topic" {
  type = string
}

variable "valid_data_topic_default_subscription" {
  type = string
}

variable "invalid_data_topic_default_subscription" {
  type = string
}

variable "valid_data_topic_subscription_for_dataflow" {
  type = string
}

variable "subscription_message_retention" {
  type = string
}

variable "storage_bucket" {
  type = string
}

variable "valid_bigquery_dataset" {
  type = string
}

variable "invalid_bigquery_dataset" {
  type = string
}

variable "invalid_bigquery_dataset_error_table_id" {
  type = string
}

variable "emails" {
  type = list(object({
    display_name = string
    email = string
    type = string
  }))
}

# load balancer variables
variable "ssl" {
  description = "Run load balancer on HTTPS and provision managed certificate with provided `domain`."
  type = bool
  default = true
}

variable "domain" {
  description = "Domain name to run the load balancer on. Used if `ssl` is `true`."
  type = string
  default = "example.com"
}

variable "lb_name" {
  description = "Name for load balancer and associated resources"
  default = "tf-cr-lb"
}

# cloud run
variable "cloud_run_api_repo" {
  type = object({
    id = string
    description = string
    format = string
  })
}

variable "cloud_run_service" {
  type = object({
    name = string
    cpu = string
    memory = string
  })
}

variable "cloud_run_container_image" {
  type = string
}