from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

TICKERS = {
    "AAPL": "Technology",
    "MSFT": "Technology",
    "GOOGL": "Technology",
    "NVDA": "Technology",
    "META": "Technology",
    "JPM": "Financials",
    "BAC": "Financials",
    "GS": "Financials",
    "V": "Financials",
    "JNJ": "Healthcare",
    "UNH": "Healthcare",
    "PFE": "Healthcare",
    "XOM": "Energy",
    "CVX": "Energy",
    "COP": "Energy",
    "AMZN": "Consumer Discretionary",
    "TSLA": "Consumer Discretionary",
    "WMT": "Consumer Staples",
    "KO": "Consumer Staples",
    "PG": "Consumer Staples",
}


def fetch_stock_data(
    tickers: dict[str, str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    output_dir: str = "/opt/airflow/data/raw",
) -> str:
    pass
