variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "location" {
  type    = string
  default = "US"
}

variable "gcs_bucket_name" {
  type    = string
  default = "stock-market-data-lake"
}

variable "bq_dataset_name" {
  type    = string
  default = "stock_market"
}
