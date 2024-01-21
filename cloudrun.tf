provider "google-beta" {
  project = var.project_id
  credentials = file("credentials.json")
  region = var.location
}

module "lb-http" {
  source  = "terraform-google-modules/lb-http/google//modules/serverless_negs"
  version = "~> 10.0"

  name    = var.lb_name
  project = var.project_id

  ssl                             = var.ssl
  managed_ssl_certificate_domains = [var.domain]
  https_redirect                  = var.ssl
  labels                          = { "example-label" = "cloud-run-example" }

  backends = {
    default = {
      description = null
      groups = [
        {
          group = google_compute_region_network_endpoint_group.serverless_neg.id
        }
      ]
      enable_cdn = false

      iap_config = {
        enable = false
      }
      log_config = {
        enable = false
      }
    }
  }
}

resource "google_compute_region_network_endpoint_group" "serverless_neg" {
  provider              = google-beta
  name                  = "serverless-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.location
  cloud_run {
    service = google_cloud_run_v2_service.cloud-run-api-service.name
  }
}

# cloud run api service
resource "google_cloud_run_v2_service" "cloud-run-api-service" {
  name     = var.cloud_run_service.name
  location = var.location
  ingress = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

  template {
    containers {
      image = var.cloud_run_container_image
      resources {
        limits = {
          cpu    = var.cloud_run_service.cpu
          memory = var.cloud_run_service.memory
        }
      }
    }
  }
}

# make cloud run service public (no-auth)
data "google_iam_policy" "no-auth" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }
}

resource "google_cloud_run_service_iam_policy" "no-auth-iam-policy" {
  location    = google_cloud_run_v2_service.cloud-run-api-service.location
  project     = google_cloud_run_v2_service.cloud-run-api-service.project
  service     = google_cloud_run_v2_service.cloud-run-api-service.name

  policy_data = data.google_iam_policy.no-auth.policy_data
}

output "service_url" {
  value       = google_cloud_run_v2_service.cloud-run-api-service.uri
  description = "The URL on which the deployed service is available"
}

output "load-balancer-ip" {
  value = module.lb-http.external_ip
}