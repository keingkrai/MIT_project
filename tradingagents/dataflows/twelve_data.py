import os
import pandas as pd
from datetime import datetime
from typing import Annotated
from twelvedata import TDClient

def get_twelvedata_stock(
    symbol: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
    interval: Annotated[str, "Interval for data, e.g., 1day, 1week, 1month"] = "1d",
):
    api_key = os.getenv("TWELVEDATA_API_KEY")
    # api_key = "e74d6f8538fa40cabdc1dec473592c9a"
    if not api_key:
        return "Missing TWELVEDATA_API_KEY in .env"

    td = TDClient(apikey=api_key)

    # TwelveData interval mapping (1d/1w/1M แบบของคุณ → twelvedata ใช้ “1day”, “1week”, “1month”)
    interval_map = {
        "1d": "1day",
        "1w": "1week",
        "1M": "1month"
    }
    if interval not in interval_map:
        return f"Invalid interval. Supported: {list(interval_map.keys())}"

    td_interval = interval_map[interval]

    # ดึง data จาก API
    ts = td.time_series(
        symbol=symbol,
        interval=td_interval,
        start_date=start_date,
        end_date=end_date,
        outputsize=5000,  # จำนวนจุดข้อมูล
        timezone="Exchange"  # ใช้ timezone ของตลาด (เช่น NASDAQ)
    )

    # ดึงเป็น pandas DataFrame
    df = ts.as_pandas()

    if df is None or df.empty:
        return f"No data found for {symbol} in TwelveData between {start_date} and {end_date}"

    # Tweak: rename columnให้เหมือน Alpha Vantage แบบก่อน
    # TwelveData ส่งชื่อ columns เป็น open, high, low, close, volume
    df = df.rename(columns={
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "volume": "Volume"
    })

    # round ค่าเหมือนโค้ดเดิม
    df["Open"] = df["Open"].round(2)
    df["High"] = df["High"].round(2)
    df["Low"] = df["Low"].round(2)
    df["Close"] = df["Close"].round(2)
    df["Volume"] = df["Volume"].fillna(0).astype(int)

    # สร้าง CSV string
    csv_string = df.to_csv(index_label="Date")

    # สร้าง header
    header = (
        f"# TwelveData data for {symbol.upper()} from {start_date} to {end_date}\n"
        f"# Interval: {interval}\n"
        f"# Total records: {len(df)}\n"
        f"# Retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    )

    return header, csv_string
    # return header + csv_string

# print(get_twelvedata_stock(
#     "AAPL",
#     "2024-11-17",
#     "2025-11-17"
# ))