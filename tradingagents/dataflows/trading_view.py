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
    # tv = TvDatafeed(username=os.getenv('TV_USERNAME'), password=os.getenv('TV_PASSWORD'))
    tv = TvDatafeed()

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



# ===== get indicators =====

import os
from tvDatafeed import TvDatafeed, Interval
from stockstats import wrap
from datetime import datetime, timedelta
import pandas as pd

# สร้าง object สำหรับ login TradingView (anonymous ก็ได้)


def get_tradingview_indicators(symbol, indicator, curr_date, look_back_days = 30, exchange='NASDAQ'):

    indicator_descriptions = {
        "close_50_sma": "50 SMA: A medium-term trend indicator. Usage: Identify trend direction and serve as dynamic support/resistance. Tips: It lags price; combine with faster indicators for timely signals.",
        "close_200_sma": "200 SMA: A long-term trend benchmark. Usage: Confirm overall market trend and identify golden/death cross setups. Tips: It reacts slowly; best for strategic trend confirmation rather than frequent trading entries.",
        "close_10_ema": "10 EMA: A responsive short-term average. Usage: Capture quick shifts in momentum and potential entry points. Tips: Prone to noise in choppy markets; use alongside longer averages for filtering false signals.",
        "macd": "MACD: Computes momentum via differences of EMAs. Usage: Look for crossovers and divergence as signals of trend changes. Tips: Confirm with other indicators in low-volatility or sideways markets.",
        "macds": "MACD Signal: An EMA smoothing of the MACD line. Usage: Use crossovers with the MACD line to trigger trades. Tips: Should be part of a broader strategy to avoid false positives.",
        "macdh": "MACD Histogram: Shows the gap between the MACD line and its signal. Usage: Visualize momentum strength and spot divergence early. Tips: Can be volatile; complement with additional filters in fast-moving markets.",
        "rsi": "RSI: Measures momentum to flag overbought/oversold conditions. Usage: Apply 70/30 thresholds and watch for divergence to signal reversals. Tips: In strong trends, RSI may remain extreme; always cross-check with trend analysis.",
        "boll": "Bollinger Middle: A 20 SMA serving as the basis for Bollinger Bands. Usage: Acts as a dynamic benchmark for price movement. Tips: Combine with the upper and lower bands to effectively spot breakouts or reversals.",
        "boll_ub": "Bollinger Upper Band: Typically 2 standard deviations above the middle line. Usage: Signals potential overbought conditions and breakout zones. Tips: Confirm signals with other tools; prices may ride the band in strong trends.",
        "boll_lb": "Bollinger Lower Band: Typically 2 standard deviations below the middle line. Usage: Indicates potential oversold conditions. Tips: Use additional analysis to avoid false reversal signals.",
        "atr": "ATR: Averages true range to measure volatility. Usage: Set stop-loss levels and adjust position sizes based on current market volatility. Tips: It's a reactive measure, so use it as part of a broader risk management strategy.",
        "vwma": "VWMA: A moving average weighted by volume. Usage: Confirm trends by integrating price action with volume data. Tips: Watch for skewed results from volume spikes; use in combination with other volume analyses."
    }

    tv = TvDatafeed(username=os.getenv('TV_USERNAME'), password=os.getenv('TV_PASSWORD'))

    curr_dt = datetime.strptime(curr_date, "%Y-%m-%d")
    before_dt = curr_dt - timedelta(days=look_back_days)

    # ดึงข้อมูล OHLC จาก TV
    df = tv.get_hist(symbol, exchange, interval=Interval.in_daily, n_bars=look_back_days + 100)
    if df.empty:
        return f"No data found for {symbol}"

    df = df.reset_index()  # datetime index → column 'datetime'
    df['datetime'] = pd.to_datetime(df['datetime'])

    # wrap เฉพาะ OHLC + volume
    df_wrap = df[['open', 'high', 'low', 'close', 'volume']].copy()
    df_wrap = wrap(df_wrap)

    # trigger calculation indicator
    try:
        df_wrap[indicator]
    except Exception as e:
        return f"Indicator {indicator} not available: {e}"

    # merge indicator กลับกับ datetime
    df[indicator] = df_wrap[indicator]

    # filter วันย้อนหลัง
    df_filtered = df[df['datetime'] <= curr_dt].tail(look_back_days + 1)

    df_filtered = df_filtered[df_filtered['datetime'] >= before_dt]

    # สร้าง string output
    ind_string = ""
    for _, row in df_filtered.iterrows():
        value = row[indicator]
        value = "N/A" if pd.isna(value) else value
        ind_string += f"{row['datetime'].strftime('%Y-%m-%d')}: {value}\n"

    # รวมผลลัพธ์ + description
    result_str = (
        f"\n\n=== tradingview ===\n## {indicator.upper()} values from {before_dt.strftime('%Y-%m-%d')} to {curr_date}:\n\n"
        + ind_string
        + "\n\n"
        + indicator_descriptions.get(indicator, "No description available.")
    )

    return result_str, df_filtered


# ตัวอย่างเรียกใช้งาน
# print(get_tradingview_indicators("AAPL", "close_50_sma", "2025-11-25", 30))