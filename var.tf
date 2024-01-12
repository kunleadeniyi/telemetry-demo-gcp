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