import os
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
    if tickers is None:
        tickers = TICKERS

    if start_date is None:
        start_date = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")

    print(f"Fetching data for {len(tickers)} tickers from {start_date} to {end_date}")

    all_data = []

    for ticker, sector in tickers.items():
        print(f"  Downloading {ticker} ({sector})...")
        try:
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        except Exception as e:
            print(f"  ERROR: {ticker}: {e}")
            continue

        if df.empty:
            print(f"  WARNING: No data for {ticker}")
            continue

        df = df.reset_index()
        # yfinance 1.x returns MultiIndex columns like ('Close', 'AAPL') — flatten them
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        df.columns = [c.lower() for c in df.columns]
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df["ticker"] = ticker
        df["sector"] = sector

        df = df[["date", "ticker", "sector", "open", "high", "low", "close", "volume"]]
        all_data.append(df)
        print(f"    {ticker}: {len(df)} rows")

    if not all_data:
        raise ValueError("No stock data fetched.")

    combined = pd.concat(all_data, ignore_index=True)
    combined = combined.sort_values(["date", "ticker"]).reset_index(drop=True)

    print(f"\nTotal records: {len(combined)}")
    print(f"Tickers fetched: {combined['ticker'].nunique()}/{len(tickers)}")

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"stocks_{timestamp}.parquet")
    combined.to_parquet(output_path, index=False, engine="pyarrow", compression=None)
    print(f"Saved to {output_path}")

    return output_path


if __name__ == "__main__":
    fetch_stock_data(output_dir="data/raw")
