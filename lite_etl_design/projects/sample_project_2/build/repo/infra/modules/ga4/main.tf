# modules/ga4 - the GCP service account the ga4_extract job uses to read the
# GA4 BigQuery export. ref: deployment-and-iac.md s.1
#
# Phase 4 scaffold. The SA key is NOT created here in the long run - it is
# rotated in AWS Secrets Manager; this module manages the SA + IAM bindings.

terraform {
  required_providers {
    google = { source = "hashicorp/google", version = "~> 5.40" }
  }
}

resource "google_service_account" "ga4_reader" {
  project      = var.gcp_project_id # TODO
  account_id   = "northwind-${var.env}-ga4-reader"
  display_name = "Northwind ${var.env} GA4 BigQuery reader"
}

resource "google_project_iam_member" "bq_data_viewer" {
  project = var.gcp_project_id
  role    = "roles/bigquery.dataViewer"
  member  = "serviceAccount:${google_service_account.ga4_reader.email}"
}

resource "google_project_iam_member" "bq_job_user" {
  project = var.gcp_project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.ga4_reader.email}"
}

# TODO: key material is generated out-of-band and stored in Secrets Manager at
# northwind/<env>/ga4#credentials_json. Prefer Workload Identity Federation if the
# extractor runs on ECS. Do not commit a key.
