# Stock Market Data Pipeline

An end-to-end batch data pipeline that ingests daily OHLCV (open, high, low, close, volume)
data for 20 US stocks across 5 sectors, stores it in Google Cloud Storage as Parquet,
loads it into BigQuery, runs dbt transformations, and serves a Streamlit analytics dashboard.

Built as a portfolio project to demonstrate production-style data engineering practices:
infrastructure as code, workflow orchestration, layered dbt modelling, and a custom
visualisation layer.

## Architecture

```
Yahoo Finance (yfinance)
        │
        ▼
  Apache Airflow DAG (daily schedule)
        │
        ├─► Google Cloud Storage (Parquet, data lake)
        │
        ├─► BigQuery raw table (partitioned by date, clustered by ticker/sector)
        │
        ├─► dbt (staging + mart models)
        │
        └─► Streamlit dashboard (Plotly charts)
```

Infrastructure provisioned with Terraform. All services run locally via Docker Compose.

## Dataset

Daily OHLCV data for 20 US stocks across 5 sectors:

| Sector | Tickers |
|---|---|
| Technology | AAPL, MSFT, GOOGL, NVDA, META |
| Financials | JPM, BAC, GS, V |
| Healthcare | JNJ, UNH, PFE |
| Energy | XOM, CVX, COP |
| Consumer | AMZN, TSLA, WMT, KO, PG |

Approximately 2 years of history (~14,600 rows on first run).

## Tech Stack

| Layer | Tool |
|---|---|
| Orchestration | Apache Airflow 2.9 |
| Ingestion | yfinance, PyArrow |
| Data lake | Google Cloud Storage (Parquet) |
| Data warehouse | BigQuery (partitioned + clustered) |
| Transformations | dbt-bigquery |
| Dashboard | Streamlit + Plotly |
| IaC | Terraform |
| Containerisation | Docker Compose |

## dbt Models

**Staging**
- `stg_stock_prices` — cleans raw data, casts types, deduplicates by (ticker, date)

**Marts**
- `fct_daily_returns` — daily and cumulative percentage returns, daily price range
- `fct_moving_averages` — 7/30/90 day SMAs, 20-day rolling volatility
- `fct_sector_performance` — sector-level aggregations, cumulative returns, daily ranking

All mart models are materialised as tables. All models have dbt schema tests (not_null, unique).

## BigQuery Table Design

The raw table `raw_stock_prices` is:
- **Partitioned** by `date` (DAY) — queries filtered by date scan only the relevant partition
- **Clustered** by `ticker`, `sector` — reduces bytes scanned within each partition

This keeps query costs low and performance fast even as the table grows.

## Prerequisites

- Docker and Docker Compose
- Terraform >= 1.0
- Google Cloud SDK (`gcloud`) — for authenticating Terraform
- A GCP project with a service account that has **BigQuery Admin** and **Storage Admin** roles

## How to Run

### 1. Clone and set up

```bash
git clone https://github.com/hnrad98/Stock-Market-Data-Pipeline.git
cd Stock-Market-Data-Pipeline
make setup
```

This creates `.env` from the template and sets up required directories.

### 2. Configure environment

Edit `.env` with your real values before continuing — step 3 sources this file:

```bash
GCP_PROJECT_ID=your-actual-project-id
GCS_BUCKET_NAME=stock-market-data-lake-your-actual-project-id
BQ_DATASET=stock_market
GCP_KEY_PATH=./keys
```

Place your GCP service account key at `./keys/gcp-key.json`.

### 3. Provision GCP infrastructure

If you haven't authenticated gcloud before, do this once:

```bash
gcloud auth application-default login
```

This opens a browser login and writes a local credentials file that Terraform picks up automatically.

Then:

```bash
source .env
export GCP_PROJECT_ID
make terraform-init
make terraform-apply
```

`source .env` loads the variables into your shell. `export GCP_PROJECT_ID` makes it available
to subprocesses (Terraform, Docker Compose). This creates the GCS bucket and BigQuery dataset.

### 4. Start services

```bash
make up
```

Wait about 30 seconds for Airflow to initialise, then open http://localhost:8080.

Airflow credentials: `admin` / `admin`

### 5. Run the pipeline

In the Airflow UI, unpause and trigger the `stock_market_pipeline` DAG.

The DAG runs 5 tasks in sequence:
1. `fetch_stock_data` — downloads OHLCV data via yfinance, saves as Parquet
2. `upload_to_gcs` — uploads Parquet file to GCS data lake
3. `gcs_to_bigquery` — loads from GCS into BigQuery raw table
4. `dbt_run` — runs all dbt models
5. `dbt_test` — runs dbt schema tests

### 6. View the dashboard

Once the DAG completes, open http://localhost:8501.

## Useful Commands

```bash
make help              # list all available make targets
make up                # start all services
make down              # stop all services
make logs              # tail all container logs
make dbt-run           # run dbt models manually
make dbt-test          # run dbt tests manually
make terraform-destroy # tear down all GCP resources
```

## Project Structure

```
├── airflow/
│   ├── dags/stock_pipeline_dag.py   # Airflow DAG definition
│   └── requirements.txt             # Airflow Python dependencies
├── dashboard/
│   └── app.py                       # Streamlit dashboard
├── dbt_stocks/
│   └── models/
│       ├── staging/                 # Cleaning and standardisation layer
│       └── marts/                   # Business logic and aggregations
├── ingestion/
│   ├── fetch_stocks.py              # yfinance download logic
│   └── upload_to_gcs.py             # GCS upload logic
└── terraform/
    ├── main.tf                      # GCS bucket + BigQuery dataset
    └── variables.tf                 # Configurable variables
```

## License

MIT
