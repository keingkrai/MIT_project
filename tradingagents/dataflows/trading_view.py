from typing import Annotated
from tvDatafeed import TvDatafeed, Interval
from datetime import datetime
import pandas as pd
import dotenv
import os

def get_TV_data_online(
    symbol: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
    exchange: Annotated[str, "Exchange code, e.g., NASDAQ"] = "NASDAQ",
    interval: Annotated[str, "Interval for data, e.g., 1d, 1h"] = "1d",
):
    dotenv.load_dotenv()
    tv = TvDatafeed(username=os.getenv('TV_USERNAME'), password=os.getenv('TV_PASSWORD'))

    # Validate date
    datetime.strptime(start_date, "%Y-%m-%d")
    datetime.strptime(end_date, "%Y-%m-%d")

    # Interval mapping
    interval_map = {
        "1m": Interval.in_1_minute,
        "5m": Interval.in_5_minute,
        "15m": Interval.in_15_minute,
        "1h": Interval.in_1_hour,
        "4h": Interval.in_4_hour,
        "1d": Interval.in_daily,
        "1w": Interval.in_weekly,
        "1M": Interval.in_monthly,
    }

    if interval not in interval_map:
        return f"Invalid interval. Supported: {list(interval_map.keys())}"

    # Fetch data
    data = tv.get_hist(
        symbol=symbol,
        exchange=exchange,
        interval=interval_map[interval],
        n_bars=5000
    )

    if data is None or data.empty:
        return f"No data found for symbol '{symbol}' from TradingView"

    # Filter by date
    data = data.loc[start_date:end_date]

    if data.empty:
        return f"No data found for symbol '{symbol}' between {start_date} and {end_date}"

    # Remove timezone
    if data.index.tz:
        data.index = data.index.tz_localize(None)
    
    # Convert datetime index -> date index
    data.index = data.index.date

    # Rename columns to match Yahoo Finance style
    data = data.rename(columns={
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "volume": "Volume"
    })

    # print(data.head())

    # example result
    #                  symbol    Open      High       Low   Close      Volume  
    #  2024-11-18  NASDAQ:AAPL  225.25  229.7400  225.1700  228.02  44686020.0  

    # Add Adj Close = Close (TV ไม่มีค่านี้)
    # data["Adj Close"] = data["Close"]

    # Reorder columns to match Yahoo
    ordered_cols = ["Open", "High", "Low", "Close", "Volume"]
    data = data[ordered_cols]

    # Round numeric columns
    for col in ["Open", "High", "Low", "Close"]:
        data[col] = data[col].round(2)
    
    data["Volume"] = data["Volume"].astype(int)

    # Convert to CSV
    csv_string = data.to_csv(index_label="Date")

    # Header (เหมือนเดิม)
    header = (
        f"# Stock data for {symbol.upper()} from {start_date} to {end_date}\n"
        f"# Total records: {len(data)}\n"
        f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    )

    # return header + csv_string
    return header, csv_string

# print(get_TV_data_online("AAPL", "NASDAQ", "1d", "2024-11-17", "2025-11-17"))