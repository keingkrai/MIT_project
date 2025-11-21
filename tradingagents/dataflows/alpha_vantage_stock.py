from datetime import datetime
from typing import Annotated
from .alpha_vantage_common import _make_api_request, _filter_csv_by_date_range

# def get_stock(
#     symbol: str,
#     start_date: str,
#     end_date: str
# ) -> str:
#     """
#     Returns raw daily OHLCV values, adjusted close values, and historical split/dividend events
#     filtered to the specified date range.

#     Args:
#         symbol: The name of the equity. For example: symbol=IBM
#         start_date: Start date in yyyy-mm-dd format
#         end_date: End date in yyyy-mm-dd format

#     Returns:
#         CSV string containing the daily adjusted time series data filtered to the date range.
#     """
#     # Parse dates to determine the range
#     start_dt = datetime.strptime(start_date, "%Y-%m-%d")
#     today = datetime.now()

#     # Choose outputsize based on whether the requested range is within the latest 100 days
#     # Compact returns latest 100 data points, so check if start_date is recent enough
#     days_from_today_to_start = (today - start_dt).days
#     outputsize = "compact" if days_from_today_to_start < 100 else "full"

#     params = {
#         "symbol": symbol,
#         "outputsize": outputsize,
#         "datatype": "csv",
#     }

#     response = _make_api_request("TIME_SERIES_DAILY_ADJUSTED", params)

#     return _filter_csv_by_date_range(response, start_date, end_date)

import os
from alpha_vantage.timeseries import TimeSeries
import pandas as pd
from datetime import datetime

def get_alpha_vantage_stock(
    symbol: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
    interval: Annotated[str, "Interval for data, e.g., 1d, 1w, 1M"] = "1d",
):
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")

    if not api_key:
        return "Missing ALPHA_VANTAGE_API_KEY in .env"

    # Validate dates
    sd = datetime.strptime(start_date, "%Y-%m-%d")
    ed = datetime.strptime(end_date, "%Y-%m-%d")

    interval_map = {
        "1d": "daily",
        "1w": "weekly",
        "1M": "monthly"
    }

    if interval not in interval_map:
        return f"Invalid interval. Supported: {list(interval_map.keys())}"

    ts = TimeSeries(key=api_key, output_format='pandas')

    # Fetch data
    if interval == "1d":
        df, meta = ts.get_daily(symbol=symbol, outputsize='full')
    elif interval == "1w":
        df, meta = ts.get_weekly(symbol=symbol)
    elif interval == "1M":
        df, meta = ts.get_monthly(symbol=symbol)

    if df is None or len(df) == 0:
        return f"No data returned for symbol {symbol}"

    # Convert index
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()  # แม้จะเรียงแล้วก็ยังต้องใช้ mask

    # ---- FIX: ใช้ mask แทน .loc ----
    df = df[(df.index >= sd) & (df.index <= ed)]

    if df.empty:
        return f"No data found for {symbol} between {start_date} and {end_date}"

    rename_map = {
        "1. open": "Open",
        "2. high": "High",
        "3. low": "Low",
        "4. close": "Close",
        "5. volume": "Volume"
    }
    df = df.rename(columns=rename_map)

    # Drop adjusted closes
    df = df.drop(columns=[c for c in df.columns if "adjusted" in c.lower()], errors='ignore')

    df = df[["Open", "High", "Low", "Close", "Volume"]]

    # Clean data
    df["Open"] = df["Open"].astype(float).round(2)
    df["High"] = df["High"].astype(float).round(2)
    df["Low"] = df["Low"].astype(float).round(2)
    df["Close"] = df["Close"].astype(float).round(2)
    df["Volume"] = df["Volume"].fillna(0).astype(int)

    csv_string = df.to_csv(index_label="Date")

    header = (
        f"# Alpha Vantage data for {symbol.upper()} from {start_date} to {end_date}\n"
        # f"# Interval: {interval}\n"
        f"# Total records: {len(df)}\n"
        f"# Retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    )

    # return header + csv_string
    return header, csv_string

# print(get_stock(
#     "AAPL",
#     "1d",
#     "2024-11-17", 
#     "2025-11-17"
# ))