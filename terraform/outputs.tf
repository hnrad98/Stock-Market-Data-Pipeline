output "gcs_bucket_name" {
  value = google_storage_bucket.data_lake.name
}

output "gcs_bucket_url" {
  value = google_storage_bucket.data_lake.url
}

output "bigquery_dataset_id" {
  value = google_bigquery_dataset.stock_market.dataset_id
}
