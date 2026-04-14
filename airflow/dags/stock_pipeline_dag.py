import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

import sys
sys.path.insert(0, "/opt/airflow")

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


def _fetch_stock_data(**context):
    from ingestion.fetch_stocks import fetch_stock_data

    output_path = fetch_stock_data(output_dir=RAW_DATA_DIR)
    context["ti"].xcom_push(key="parquet_path", value=output_path)
    print(f"fetch_stock_data completed: parquet saved to {output_path}")


def _upload_to_gcs(**context):
    from ingestion.upload_to_gcs import upload_to_gcs

    parquet_path = context["ti"].xcom_pull(
        task_ids="fetch_stock_data", key="parquet_path"
    )
    gcs_uri = upload_to_gcs(
        local_path=parquet_path,
        bucket_name=GCS_BUCKET_NAME,
    )
    context["ti"].xcom_push(key="gcs_uri", value=gcs_uri)


def _gcs_to_bigquery(**context):
    from google.cloud import bigquery

    gcs_uri = context["ti"].xcom_pull(
        task_ids="upload_to_gcs", key="gcs_uri"
    )

    client = bigquery.Client(project=GCP_PROJECT_ID)
    table_id = f"{GCP_PROJECT_ID}.{BQ_DATASET}.raw_stock_prices"

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        time_partitioning=bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="date",
        ),
        clustering_fields=["ticker", "sector"],
    )

    print(f"Loading {gcs_uri} into {table_id}")
    load_job = client.load_table_from_uri(gcs_uri, table_id, job_config=job_config)
    load_job.result()

    table = client.get_table(table_id)
    print(f"Loaded {table.num_rows} rows into {table_id}")


with DAG(
    dag_id="stock_market_pipeline",
    default_args=default_args,
    description="Ingest stock market data: Yahoo Finance -> GCS -> BigQuery -> dbt",
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["stocks", "finance", "pipeline"],
) as dag:

    fetch_task = PythonOperator(
        task_id="fetch_stock_data",
        python_callable=_fetch_stock_data,
    )

    upload_task = PythonOperator(
        task_id="upload_to_gcs",
        python_callable=_upload_to_gcs,
    )

    load_bq_task = PythonOperator(
        task_id="gcs_to_bigquery",
        python_callable=_gcs_to_bigquery,
    )

    dbt_run_task = BashOperator(
        task_id="dbt_run",
        bash_command=(
            "cd /opt/airflow/dbt_stocks && "
            "dbt run --profiles-dir . --project-dir . --target prod"
        ),
    )

    dbt_test_task = BashOperator(
        task_id="dbt_test",
        bash_command=(
            "cd /opt/airflow/dbt_stocks && "
            "dbt test --profiles-dir . --project-dir . --target prod"
        ),
    )

    fetch_task >> upload_task >> load_bq_task >> dbt_run_task >> dbt_test_task
