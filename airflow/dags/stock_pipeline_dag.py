import os
from datetime import datetime, timedelta

from airflow import DAG

GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME")
BQ_DATASET = os.environ.get("BQ_DATASET", "stock_market")
RAW_DATA_DIR = "/opt/airflow/data/raw"

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=3),
}

with DAG(
    dag_id="stock_market_pipeline",
    default_args=default_args,
    description="Ingest stock market data: Yahoo Finance -> GCS -> BigQuery -> dbt",
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["stocks", "finance", "pipeline"],
) as dag:
    pass
