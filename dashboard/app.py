import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from google.cloud import bigquery

PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
DATASET = os.environ.get("BQ_DATASET", "stock_market")

st.set_page_config(
    page_title="Stock Market Analytics",
    page_icon="📈",
    layout="wide",
)


@st.cache_resource
def get_bq_client():
    return bigquery.Client(project=PROJECT_ID)


@st.cache_data(ttl=3600)
def run_query(query: str) -> pd.DataFrame:
    client = get_bq_client()
    return client.query(query).to_dataframe()


def load_daily_returns() -> pd.DataFrame:
    query = f"""
    SELECT trade_date, ticker, sector, close_price, volume,
           daily_return_pct, cumulative_return_pct, daily_range_pct
    FROM `{PROJECT_ID}.{DATASET}.fct_daily_returns`
    ORDER BY trade_date DESC
    """
    return run_query(query)


def load_moving_averages() -> pd.DataFrame:
    query = f"""
    SELECT trade_date, ticker, sector, close_price,
           sma_7, sma_30, sma_90,
           volatility_20d
    FROM `{PROJECT_ID}.{DATASET}.fct_moving_averages`
    ORDER BY trade_date DESC
    """
    return run_query(query)


def load_sector_performance() -> pd.DataFrame:
    query = f"""
    SELECT trade_date, sector, num_stocks, avg_daily_return,
           total_volume, cumulative_return, daily_rank
    FROM `{PROJECT_ID}.{DATASET}.fct_sector_performance`
    ORDER BY trade_date DESC
    """
    return run_query(query)


st.title("Stock Market Analytics Dashboard")
st.markdown("Data pipeline: Yahoo Finance -> GCS -> BigQuery -> dbt -> Streamlit")

try:
    df_returns = load_daily_returns()
    df_ma = load_moving_averages()
    df_sector = load_sector_performance()
except Exception as e:
    st.error(f"Failed to connect to BigQuery: {e}")
    st.info("Make sure GCP credentials are configured and the pipeline has been run.")
    st.stop()

st.sidebar.header("Filters")
tickers = sorted(df_returns["ticker"].unique())
selected_tickers = st.sidebar.multiselect(
    "Select Stocks", tickers, default=tickers[:5]
)

sectors = sorted(df_returns["sector"].unique())
selected_sectors = st.sidebar.multiselect(
    "Select Sectors", sectors, default=sectors
)

date_range = st.sidebar.date_input(
    "Date Range",
    value=(df_returns["trade_date"].min(), df_returns["trade_date"].max()),
)

mask_returns = (
    (df_returns["ticker"].isin(selected_tickers))
    & (df_returns["sector"].isin(selected_sectors))
    & (df_returns["trade_date"] >= pd.Timestamp(date_range[0]))
    & (df_returns["trade_date"] <= pd.Timestamp(date_range[1]))
)
filtered_returns = df_returns[mask_returns]

mask_ma = (
    (df_ma["ticker"].isin(selected_tickers))
    & (df_ma["trade_date"] >= pd.Timestamp(date_range[0]))
    & (df_ma["trade_date"] <= pd.Timestamp(date_range[1]))
)
filtered_ma = df_ma[mask_ma]

mask_sector = (
    (df_sector["sector"].isin(selected_sectors))
    & (df_sector["trade_date"] >= pd.Timestamp(date_range[0]))
    & (df_sector["trade_date"] <= pd.Timestamp(date_range[1]))
)
filtered_sector = df_sector[mask_sector]

st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

if not filtered_returns.empty:
    latest = filtered_returns[
        filtered_returns["trade_date"] == filtered_returns["trade_date"].max()
    ]
    best = latest.loc[latest["daily_return_pct"].idxmax()]
    worst = latest.loc[latest["daily_return_pct"].idxmin()]

    col1.metric("Best Performer (Today)", best["ticker"],
                f"{best['daily_return_pct']:.2f}%")
    col2.metric("Worst Performer (Today)", worst["ticker"],
                f"{worst['daily_return_pct']:.2f}%")
    col3.metric("Avg Daily Return", f"{latest['daily_return_pct'].mean():.2f}%")
    col4.metric("Total Stocks", len(selected_tickers))

tab1, tab2 = st.tabs([
    "Price & Moving Averages",
    "Returns Analysis",
])

with tab1:
    st.subheader("Stock Prices with Moving Averages")

    selected_stock = st.selectbox(
        "Select stock for detailed view",
        selected_tickers,
        key="ma_stock",
    )

    stock_ma = filtered_ma[filtered_ma["ticker"] == selected_stock].sort_values("trade_date")

    if not stock_ma.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=stock_ma["trade_date"], y=stock_ma["close_price"],
            name="Close Price", line=dict(color="white", width=2),
        ))
        fig.add_trace(go.Scatter(
            x=stock_ma["trade_date"], y=stock_ma["sma_7"],
            name="SMA 7", line=dict(color="cyan", width=1, dash="dot"),
        ))
        fig.add_trace(go.Scatter(
            x=stock_ma["trade_date"], y=stock_ma["sma_30"],
            name="SMA 30", line=dict(color="orange", width=1),
        ))
        fig.add_trace(go.Scatter(
            x=stock_ma["trade_date"], y=stock_ma["sma_90"],
            name="SMA 90", line=dict(color="red", width=1),
        ))
        fig.update_layout(
            title=f"{selected_stock} - Price & Moving Averages",
            xaxis_title="Date", yaxis_title="Price ($)",
            template="plotly_dark", height=500,
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("20-Day Rolling Volatility")
    vol_data = filtered_ma[filtered_ma["ticker"].isin(selected_tickers)].sort_values("trade_date")
    if not vol_data.empty:
        fig_vol = px.line(
            vol_data, x="trade_date", y="volatility_20d", color="ticker",
            title="20-Day Rolling Volatility by Stock",
            template="plotly_dark",
        )
        fig_vol.update_layout(height=400)
        st.plotly_chart(fig_vol, use_container_width=True)

with tab2:
    st.subheader("Daily Returns Comparison")

    if not filtered_returns.empty:
        fig_ret = px.line(
            filtered_returns.sort_values("trade_date"),
            x="trade_date", y="daily_return_pct", color="ticker",
            title="Daily Returns (%)",
            template="plotly_dark",
        )
        fig_ret.update_layout(height=400)
        st.plotly_chart(fig_ret, use_container_width=True)

    st.subheader("Cumulative Returns")
    if not filtered_returns.empty:
        fig_cum = px.line(
            filtered_returns.sort_values("trade_date"),
            x="trade_date", y="cumulative_return_pct", color="ticker",
            title="Cumulative Returns (%)",
            template="plotly_dark",
        )
        fig_cum.update_layout(height=400)
        st.plotly_chart(fig_cum, use_container_width=True)

    st.subheader("Returns Distribution")
    if not filtered_returns.empty:
        fig_hist = px.histogram(
            filtered_returns, x="daily_return_pct", color="ticker",
            nbins=50, title="Distribution of Daily Returns",
            template="plotly_dark", barmode="overlay", opacity=0.7,
        )
        fig_hist.update_layout(height=400)
        st.plotly_chart(fig_hist, use_container_width=True)

st.markdown("---")
st.caption(
    "Built with Streamlit | Data from Yahoo Finance | "
    "Pipeline: Airflow + GCS + BigQuery + dbt"
)
