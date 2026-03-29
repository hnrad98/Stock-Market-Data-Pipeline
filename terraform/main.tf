terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_storage_bucket" "data_lake" {
  name          = "${var.gcs_bucket_name}-${var.project_id}"
  location      = var.location
  force_destroy = true

  uniform_bucket_level_access = true
}

resource "google_bigquery_dataset" "stock_market" {
  dataset_id                 = var.bq_dataset_name
  location                   = var.location
  delete_contents_on_destroy = true

  labels = {
    environment = "dev"
    project     = "stock-pipeline"
  }
}
