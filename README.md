# Stock Market Data Pipeline

Data pipeline that pulls historical stock prices via yfinance, lands them in GCS as Parquet, loads into BigQuery, runs dbt transformations, and serves a Streamlit dashboard.

## Architecture

```
Yahoo Finance -> Airflow -> GCS (Parquet) -> BigQuery -> dbt -> Streamlit
```

## Tech Stack

Python, Apache Airflow, Google Cloud Storage, BigQuery, dbt, Streamlit, Plotly, Terraform, Docker Compose

## Dataset

Daily OHLCV data for 20 US stocks across 5 sectors (Tech, Financials, Healthcare, Energy, Consumer), ~2 years of history.

## Prerequisites

- Docker & Docker Compose
- Terraform
- GCP project with a service account key (BigQuery Admin + Storage Admin roles)

## How to Run

1. `make setup` — creates `.env` from template, sets up directories
2. Fill in `.env` with the GCP project ID and bucket name
3. Place the service account key JSON at `./keys/gcp-key.json`
4. `source .env && export GCP_PROJECT_ID` — Terraform and Docker Compose need this in the shell
5. `make terraform-init && make terraform-apply` — provisions GCS bucket + BigQuery dataset
6. `make up` — starts Airflow and the dashboard
7. Open http://localhost:8080, unpause and trigger `stock_market_pipeline`
8. Once the DAG completes, the dashboard is at http://localhost:8501

Airflow login: `admin` / `admin`

## dbt Models

- `stg_stock_prices` — cleaned raw data
- `fct_daily_returns` — daily and cumulative returns
- `fct_moving_averages` — 7/30/90 day SMAs, rolling volatility
- `fct_sector_performance` — sector-level aggregations and rankings

## Useful Commands

```bash
make help              # list all targets
make down              # stop everything
make logs              # tail all container logs
make dbt-run           # run dbt models
make terraform-destroy # tear down GCP resources
```
