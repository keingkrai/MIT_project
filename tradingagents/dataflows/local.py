from __future__ import annotations

from tkinter import END
from typing import List, Dict, Optional, Iterable, Tuple, Annotated
import pandas as pd
import os, time, json, requests, re
from .config import DATA_DIR
from datetime import datetime
from dateutil.relativedelta import relativedelta
from .reddit_utils import fetch_top_from_category
from tqdm import tqdm
from tradingview_ta import TA_Handler, Interval
from datetime import datetime, timezone
import math

def get_YFin_data_window(
    symbol: Annotated[str, "ticker symbol of the company"],
    curr_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "how many days to look back"],
) -> str:
    # calculate past days
    date_obj = datetime.strptime(curr_date, "%Y-%m-%d")
    before = date_obj - relativedelta(days=look_back_days)
    start_date = before.strftime("%Y-%m-%d")

    # read in data
    data = pd.read_csv(
        os.path.join(
            DATA_DIR,
            f"market_data/price_data/{symbol}-YFin-data-2015-01-01-2025-03-25.csv",
        )
    )

    # Extract just the date part for comparison
    data["DateOnly"] = data["Date"].str[:10]

    # Filter data between the start and end dates (inclusive)
    filtered_data = data[
        (data["DateOnly"] >= start_date) & (data["DateOnly"] <= curr_date)
    ]

    # Drop the temporary column we created
    filtered_data = filtered_data.drop("DateOnly", axis=1)

    # Set pandas display options to show the full DataFrame
    with pd.option_context(
        "display.max_rows", None, "display.max_columns", None, "display.width", None
    ):
        df_string = filtered_data.to_string()

    return (
        f"## Raw Market Data for {symbol} from {start_date} to {curr_date}:\n\n"
        + df_string
    )

def get_YFin_data(
    symbol: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    # read in data
    data = pd.read_csv(
        os.path.join(
            DATA_DIR,
            f"market_data/price_data/{symbol}-YFin-data-2015-01-01-2025-03-25.csv",
        )
    )

    if end_date > "2025-03-25":
        raise Exception(
            f"Get_YFin_Data: {end_date} is outside of the data range of 2015-01-01 to 2025-03-25"
        )

    # Extract just the date part for comparison
    data["DateOnly"] = data["Date"].str[:10]

    # Filter data between the start and end dates (inclusive)
    filtered_data = data[
        (data["DateOnly"] >= start_date) & (data["DateOnly"] <= end_date)
    ]

    # Drop the temporary column we created
    filtered_data = filtered_data.drop("DateOnly", axis=1)

    # remove the index from the dataframe
    filtered_data = filtered_data.reset_index(drop=True)

    return filtered_data

def get_finnhub_news(
    query: Annotated[str, "Search query or ticker symbol"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
):
    """
    Retrieve news about a company within a time frame

    Args
        query (str): Search query or ticker symbol
        start_date (str): Start date in yyyy-mm-dd format
        end_date (str): End date in yyyy-mm-dd format
    Returns
        str: dataframe containing the news of the company in the time frame

    """

    result = get_data_in_range(query, start_date, end_date, "news_data", DATA_DIR)

    if len(result) == 0:
        return ""

    combined_result = ""
    for day, data in result.items():
        if len(data) == 0:
            continue
        for entry in data:
            current_news = (
                "### " + entry["headline"] + f" ({day})" + "\n" + entry["summary"]
            )
            combined_result += current_news + "\n\n"

    return f"## {query} News, from {start_date} to {end_date}:\n" + str(combined_result)


def get_finnhub_company_insider_sentiment(
    ticker: Annotated[str, "ticker symbol for the company"],
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
):
    """
    Retrieve insider sentiment about a company (retrieved from public SEC information) for the past 15 days
    Args:
        ticker (str): ticker symbol of the company
        curr_date (str): current date you are trading on, yyyy-mm-dd
    Returns:
        str: a report of the sentiment in the past 15 days starting at curr_date
    """

    date_obj = datetime.strptime(curr_date, "%Y-%m-%d")
    before = date_obj - relativedelta(days=15)  # Default 15 days lookback
    before = before.strftime("%Y-%m-%d")

    data = get_data_in_range(ticker, before, curr_date, "insider_senti", DATA_DIR)

    if len(data) == 0:
        return ""

    result_str = ""
    seen_dicts = []
    for date, senti_list in data.items():
        for entry in senti_list:
            if entry not in seen_dicts:
                result_str += f"### {entry['year']}-{entry['month']}:\nChange: {entry['change']}\nMonthly Share Purchase Ratio: {entry['mspr']}\n\n"
                seen_dicts.append(entry)

    return (
        f"## {ticker} Insider Sentiment Data for {before} to {curr_date}:\n"
        + result_str
        + "The change field refers to the net buying/selling from all insiders' transactions. The mspr field refers to monthly share purchase ratio."
    )


def get_finnhub_company_insider_transactions(
    ticker: Annotated[str, "ticker symbol"],
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
):
    """
    Retrieve insider transcaction information about a company (retrieved from public SEC information) for the past 15 days
    Args:
        ticker (str): ticker symbol of the company
        curr_date (str): current date you are trading at, yyyy-mm-dd
    Returns:
        str: a report of the company's insider transaction/trading informtaion in the past 15 days
    """

    date_obj = datetime.strptime(curr_date, "%Y-%m-%d")
    before = date_obj - relativedelta(days=15)  # Default 15 days lookback
    before = before.strftime("%Y-%m-%d")

    data = get_data_in_range(ticker, before, curr_date, "insider_trans", DATA_DIR)

    if len(data) == 0:
        return ""

    result_str = ""

    seen_dicts = []
    for date, senti_list in data.items():
        for entry in senti_list:
            if entry not in seen_dicts:
                result_str += f"### Filing Date: {entry['filingDate']}, {entry['name']}:\nChange:{entry['change']}\nShares: {entry['share']}\nTransaction Price: {entry['transactionPrice']}\nTransaction Code: {entry['transactionCode']}\n\n"
                seen_dicts.append(entry)

    return (
        f"## {ticker} insider transactions from {before} to {curr_date}:\n"
        + result_str
        + "The change field reflects the variation in share count—here a negative number indicates a reduction in holdings—while share specifies the total number of shares involved. The transactionPrice denotes the per-share price at which the trade was executed, and transactionDate marks when the transaction occurred. The name field identifies the insider making the trade, and transactionCode (e.g., S for sale) clarifies the nature of the transaction. FilingDate records when the transaction was officially reported, and the unique id links to the specific SEC filing, as indicated by the source. Additionally, the symbol ties the transaction to a particular company, isDerivative flags whether the trade involves derivative securities, and currency notes the currency context of the transaction."
    )

def get_data_in_range(ticker, start_date, end_date, data_type, data_dir, period=None):
    """
    Gets finnhub data saved and processed on disk.
    Args:
        start_date (str): Start date in YYYY-MM-DD format.
        end_date (str): End date in YYYY-MM-DD format.
        data_type (str): Type of data from finnhub to fetch. Can be insider_trans, SEC_filings, news_data, insider_senti, or fin_as_reported.
        data_dir (str): Directory where the data is saved.
        period (str): Default to none, if there is a period specified, should be annual or quarterly.
    """

    if period:
        data_path = os.path.join(
            data_dir,
            "finnhub_data",
            data_type,
            f"{ticker}_{period}_data_formatted.json",
        )
    else:
        data_path = os.path.join(
            data_dir, "finnhub_data", data_type, f"{ticker}_data_formatted.json"
        )

    data = open(data_path, "r")
    data = json.load(data)

    # filter keys (date, str in format YYYY-MM-DD) by the date range (str, str in format YYYY-MM-DD)
    filtered_data = {}
    for key, value in data.items():
        if start_date <= key <= end_date and len(value) > 0:
            filtered_data[key] = value
    return filtered_data

def get_simfin_balance_sheet(
    ticker: Annotated[str, "ticker symbol"],
    freq: Annotated[
        str,
        "reporting frequency of the company's financial history: annual / quarterly",
    ],
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
):
    data_path = os.path.join(
        DATA_DIR,
        "fundamental_data",
        "simfin_data_all",
        "balance_sheet",
        "companies",
        "us",
        f"us-balance-{freq}.csv",
    )
    df = pd.read_csv(data_path, sep=";")

    # Convert date strings to datetime objects and remove any time components
    df["Report Date"] = pd.to_datetime(df["Report Date"], utc=True).dt.normalize()
    df["Publish Date"] = pd.to_datetime(df["Publish Date"], utc=True).dt.normalize()

    # Convert the current date to datetime and normalize
    curr_date_dt = pd.to_datetime(curr_date, utc=True).normalize()

    # Filter the DataFrame for the given ticker and for reports that were published on or before the current date
    filtered_df = df[(df["Ticker"] == ticker) & (df["Publish Date"] <= curr_date_dt)]

    # Check if there are any available reports; if not, return a notification
    if filtered_df.empty:
        print("No balance sheet available before the given current date.")
        return ""

    # Get the most recent balance sheet by selecting the row with the latest Publish Date
    latest_balance_sheet = filtered_df.loc[filtered_df["Publish Date"].idxmax()]

    # drop the SimFinID column
    latest_balance_sheet = latest_balance_sheet.drop("SimFinId")

    return (
        f"## {freq} balance sheet for {ticker} released on {str(latest_balance_sheet['Publish Date'])[0:10]}: \n"
        + str(latest_balance_sheet)
        + "\n\nThis includes metadata like reporting dates and currency, share details, and a breakdown of assets, liabilities, and equity. Assets are grouped as current (liquid items like cash and receivables) and noncurrent (long-term investments and property). Liabilities are split between short-term obligations and long-term debts, while equity reflects shareholder funds such as paid-in capital and retained earnings. Together, these components ensure that total assets equal the sum of liabilities and equity."
    )


def get_simfin_cashflow(
    ticker: Annotated[str, "ticker symbol"],
    freq: Annotated[
        str,
        "reporting frequency of the company's financial history: annual / quarterly",
    ],
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
):
    data_path = os.path.join(
        DATA_DIR,
        "fundamental_data",
        "simfin_data_all",
        "cash_flow",
        "companies",
        "us",
        f"us-cashflow-{freq}.csv",
    )
    df = pd.read_csv(data_path, sep=";")

    # Convert date strings to datetime objects and remove any time components
    df["Report Date"] = pd.to_datetime(df["Report Date"], utc=True).dt.normalize()
    df["Publish Date"] = pd.to_datetime(df["Publish Date"], utc=True).dt.normalize()

    # Convert the current date to datetime and normalize
    curr_date_dt = pd.to_datetime(curr_date, utc=True).normalize()

    # Filter the DataFrame for the given ticker and for reports that were published on or before the current date
    filtered_df = df[(df["Ticker"] == ticker) & (df["Publish Date"] <= curr_date_dt)]

    # Check if there are any available reports; if not, return a notification
    if filtered_df.empty:
        print("No cash flow statement available before the given current date.")
        return ""

    # Get the most recent cash flow statement by selecting the row with the latest Publish Date
    latest_cash_flow = filtered_df.loc[filtered_df["Publish Date"].idxmax()]

    # drop the SimFinID column
    latest_cash_flow = latest_cash_flow.drop("SimFinId")

    return (
        f"## {freq} cash flow statement for {ticker} released on {str(latest_cash_flow['Publish Date'])[0:10]}: \n"
        + str(latest_cash_flow)
        + "\n\nThis includes metadata like reporting dates and currency, share details, and a breakdown of cash movements. Operating activities show cash generated from core business operations, including net income adjustments for non-cash items and working capital changes. Investing activities cover asset acquisitions/disposals and investments. Financing activities include debt transactions, equity issuances/repurchases, and dividend payments. The net change in cash represents the overall increase or decrease in the company's cash position during the reporting period."
    )


def get_simfin_income_statements(
    ticker: Annotated[str, "ticker symbol"],
    freq: Annotated[
        str,
        "reporting frequency of the company's financial history: annual / quarterly",
    ],
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
):
    data_path = os.path.join(
        DATA_DIR,
        "fundamental_data",
        "simfin_data_all",
        "income_statements",
        "companies",
        "us",
        f"us-income-{freq}.csv",
    )
    df = pd.read_csv(data_path, sep=";")

    # Convert date strings to datetime objects and remove any time components
    df["Report Date"] = pd.to_datetime(df["Report Date"], utc=True).dt.normalize()
    df["Publish Date"] = pd.to_datetime(df["Publish Date"], utc=True).dt.normalize()

    # Convert the current date to datetime and normalize
    curr_date_dt = pd.to_datetime(curr_date, utc=True).normalize()

    # Filter the DataFrame for the given ticker and for reports that were published on or before the current date
    filtered_df = df[(df["Ticker"] == ticker) & (df["Publish Date"] <= curr_date_dt)]

    # Check if there are any available reports; if not, return a notification
    if filtered_df.empty:
        print("No income statement available before the given current date.")
        return ""

    # Get the most recent income statement by selecting the row with the latest Publish Date
    latest_income = filtered_df.loc[filtered_df["Publish Date"].idxmax()]

    # drop the SimFinID column
    latest_income = latest_income.drop("SimFinId")

    return (
        f"## {freq} income statement for {ticker} released on {str(latest_income['Publish Date'])[0:10]}: \n"
        + str(latest_income)
        + "\n\nThis includes metadata like reporting dates and currency, share details, and a comprehensive breakdown of the company's financial performance. Starting with Revenue, it shows Cost of Revenue and resulting Gross Profit. Operating Expenses are detailed, including SG&A, R&D, and Depreciation. The statement then shows Operating Income, followed by non-operating items and Interest Expense, leading to Pretax Income. After accounting for Income Tax and any Extraordinary items, it concludes with Net Income, representing the company's bottom-line profit or loss for the period."
    )

def get_reddit_global_news(
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "Number of days to look back"] = 7,
    limit: Annotated[int, "Maximum number of articles to return"] = 5,
) -> str:
    """
    Retrieve the latest top reddit news
    Args:
        curr_date: Current date in yyyy-mm-dd format
        look_back_days: Number of days to look back (default 7)
        limit: Maximum number of articles to return (default 5)
    Returns:
        str: A formatted string containing the latest news articles posts on reddit
    """

    curr_date_dt = datetime.strptime(curr_date, "%Y-%m-%d")
    before = curr_date_dt - relativedelta(days=look_back_days)
    before = before.strftime("%Y-%m-%d")

    posts = []
    # iterate from before to curr_date
    curr_iter_date = datetime.strptime(before, "%Y-%m-%d")

    total_iterations = (curr_date_dt - curr_iter_date).days + 1
    pbar = tqdm(desc=f"Getting Global News on {curr_date}", total=total_iterations)

    while curr_iter_date <= curr_date_dt:
        curr_date_str = curr_iter_date.strftime("%Y-%m-%d")
        fetch_result = fetch_top_from_category(
            "global_news",
            curr_date_str,
            limit,
            data_path=os.path.join(DATA_DIR, "reddit_data"),
        )
        posts.extend(fetch_result)
        curr_iter_date += relativedelta(days=1)
        pbar.update(1)

    pbar.close()

    if len(posts) == 0:
        return ""

    news_str = ""
    for post in posts:
        if post["content"] == "":
            news_str += f"### {post['title']}\n\n"
        else:
            news_str += f"### {post['title']}\n\n{post['content']}\n\n"

    return f"## Global News Reddit, from {before} to {curr_date}:\n{news_str}"

def get_reddit_companynews(
    query: Annotated[str, "Search query or ticker symbol"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """
    Retrieve the latest top reddit news
    Args:
        query: Search query or ticker symbol
        start_date: Start date in yyyy-mm-dd format
        end_date: End date in yyyy-mm-dd format
    Returns:
        str: A formatted string containing news articles posts on reddit
    """

    start_date_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_dt = datetime.strptime(end_date, "%Y-%m-%d")

    posts = []
    # iterate from start_date to end_date
    curr_date = start_date_dt

    total_iterations = (end_date_dt - curr_date).days + 1
    pbar = tqdm(
        desc=f"Getting Company News for {query} from {start_date} to {end_date}",
        total=total_iterations,
    )

    while curr_date <= end_date_dt:
        curr_date_str = curr_date.strftime("%Y-%m-%d")
        fetch_result = fetch_top_from_category(
            "company_news",
            curr_date_str,
            10,  # max limit per day
            query,
            data_path=os.path.join(DATA_DIR, "reddit_data"),
        )
        posts.extend(fetch_result)
        curr_date += relativedelta(days=1)

        pbar.update(1)

    pbar.close()

    if len(posts) == 0:
        return ""

    news_str = ""
    for post in posts:
        if post["content"] == "":
            news_str += f"### {post['title']}\n\n"
        else:
            news_str += f"### {post['title']}\n\n{post['content']}\n\n"

    return f"##{query} News Reddit, from {start_date} to {end_date}:\n\n{news_str}"

#------------------------------ EDIT INDICATORS ---------------------------------#

_INTERVAL_MAP = {
    "1m":  Interval.INTERVAL_1_MINUTE,
    "5m":  Interval.INTERVAL_5_MINUTES,
    "15m": Interval.INTERVAL_15_MINUTES,
    "30m": Interval.INTERVAL_30_MINUTES,
    "1h":  Interval.INTERVAL_1_HOUR,
    "4h":  Interval.INTERVAL_4_HOURS,
    "1d":  Interval.INTERVAL_1_DAY,
    "1w":  Interval.INTERVAL_1_WEEK,
    "1mo": Interval.INTERVAL_1_MONTH,
}

def _to_interval(interval_str: str) -> Interval:
    i = interval_str.lower().strip()
    if i not in _INTERVAL_MAP:
        raise ValueError(f"Unsupported interval '{interval_str}'. Use one of: {', '.join(_INTERVAL_MAP.keys())}")
    return _INTERVAL_MAP[i]

# ต้องมี (ถ้ายังไม่ได้ import)
from tradingview_ta import TA_Handler, Interval
from datetime import datetime

# ====== กำหนดรายการที่ต้องการโชว์ + alias ======
REQUESTED_INDICATORS = {
    "close_50_sma":   ("50 SMA", "close"),
    "close_200_sma":  ("200 SMA", "close"),
    "close_10_ema":   ("10 EMA", "close"),
    "macd":           ("MACD", "close"),
    "macds":          ("MACD Signal", "close"),
    "macdh":          ("MACD Histogram", "close"),
    "rsi":            ("RSI", "close"),
    "boll":           ("Bollinger Middle", "close"),
    "boll_ub":        ("Bollinger Upper Band", "close"),
    "boll_lb":        ("Bollinger Lower Band", "close"),
    "atr":            ("ATR", None),
    "vwma":           ("VWMA", "close"),
}

INDICATOR_ALIASES = {
    "close_50_sma":  ["SMA50", "sma50", "MA50", "ma50"],
    "close_200_sma": ["SMA200", "sma200", "MA200", "ma200"],
    "close_10_ema":  ["EMA10", "ema10"],
    "macd":          ["MACD.macd", "macd", "MACD"],
    "macds":         ["MACD.signal", "macds", "MACDSignal", "signal"],
    "macdh":         ["MACD.hist", "macdh", "MACDHistogram", "histogram"],
    "rsi":           ["RSI", "rsi", "RSI[14]"],
    "boll":          ["BB.middle", "BBasis", "BOLL_MIDDLE", "BOLL"],
    "boll_ub":       ["BB.upper", "BBUpper", "BOLL_UPPER"],
    "boll_lb":       ["BB.lower", "BBLower", "BOLL_LOWER"],
    "atr":           ["ATR", "atr", "ATR[14]"],
    "vwma":          ["VWMA", "vwma", "VWMA20"],
}

def _pick_from_indicators(ind_dict: dict, key: str):
    """คืนค่า ind_dict[key] โดยลอง alias เผื่อคีย์ไม่ตรง"""
    if key in ind_dict:
        return ind_dict[key]
    for alt in INDICATOR_ALIASES.get(key, []):
        if alt in ind_dict:
            return ind_dict[alt]
    return None


def get_tradingview_indicators_dict(
    symbol: str,
    exchange: str = "NASDAQ",
    screener: str = "america",
    interval: str = "1d",
) -> dict:
    """
    ดึงค่าจาก TradingView แล้วคืนเป็น dict ตาม key ใน REQUESTED_INDICATORS
    เช่น {"close_50_sma": 123.45, "close_200_sma": 234.56, ...}
    """
    tv_interval = _to_interval(interval)
    h = TA_Handler(
        symbol=symbol,
        screener=screener,
        exchange=exchange,
        interval=tv_interval,
    )

    # อาจโดน rate-limit หรือ symbol ผิด — กัน error ให้คืน dict ว่าง
    try:
        a = h.get_analysis()
    except Exception as e:
        # ถ้าอยากดีบักก็ print(e) ได้
        return {}

    ind = a.indicators or {}
    out = {}
    for key in REQUESTED_INDICATORS.keys():
        v = _pick_from_indicators(ind, key)
        try:
            out[key] = float(v) if v is not None else None
        except Exception:
            out[key] = None
    return out


def get_tradingview_indicators(
    symbol: str,
    exchange: str = "NASDAQ",
    screener: str = "america",
    interval: str = "1d",
) -> str:
    """
    เวอร์ชันเดิม (คืน Markdown) แต่ภายในเรียก dict เวอร์ชันเพื่อให้รูปแบบข้อมูลสอดคล้อง
    """
    data = get_tradingview_indicators_dict(
        symbol=symbol, exchange=exchange, screener=screener, interval=interval
    )

    header  = f"# TradingView TA for {symbol.upper()} ({exchange}) [{interval}]\n"
    header += f"# Screener: {screener}\n"
    header += f"# Retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    lines = []
    lines.append("## INDICATORS (numeric)")
    if not data:
        lines.append("(no indicators)")
        lines.append("")
        return header + "\n".join(lines)

    lines.append("| Indicator | Value |")
    lines.append("|---|---|")

    any_found = False
    for key, (display_name, _src) in REQUESTED_INDICATORS.items():
        v = data.get(key, None)
        if v is None:
            val_str = "–"
        else:
            any_found = True
            val_str = f"{v:.4f}"
        lines.append(f"| {display_name} | {val_str} |")

    if not any_found:
        lines.append("| (no indicators found) | - |")
    lines.append("")

    body = "\n".join(lines)
    return header + body


# ----------------------------- yfinance INDICATORS ----------------------------- #
# pip install yfinance pandas ta
import pandas as pd
import yfinance as yf
from typing import Dict, Optional

from ta.trend import EMAIndicator, SMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands, AverageTrueRange

# ใช้ mapping/alias เดิมที่คุณประกาศไว้ก่อนหน้า:
# REQUESTED_INDICATORS = {
#   "close_50_sma": ("50 SMA", "close"), ...
# }

def _normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """ทำชื่อคอลัมน์ให้เป็น Open/High/Low/Close/Adj Close/Volume (ถ้ามี)"""
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = df.columns.droplevel(-1)
    ren = {c: c.capitalize() for c in df.columns}
    df = df.rename(columns=ren)
    if "Adj close" in df.columns:
        df.rename(columns={"Adj close": "Adj Close"}, inplace=True)
    return df

def _ensure_basic_columns(df: pd.DataFrame) -> pd.DataFrame:
    """ให้แน่ใจว่ามีคอลัมน์หลักครบ ถ้าไม่มี Volume ให้เติม 0"""
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        if col not in df.columns:
            if col == "Volume":
                df["Volume"] = 0
            else:
                raise RuntimeError(f"Missing column: {col}")
    return df

def _compute_indicators_yf(
    df: pd.DataFrame,
    ema_window: int = 10,
    sma50_window: int = 50,
    sma200_window: int = 200,
    rsi_window: int = 14,
    bb_window: int = 20,
    bb_dev: float = 2.0,
    atr_window: int = 14,
    vwma_window: int = 20,
) -> pd.DataFrame:
    """คำนวณอินดิเคเตอร์ตามชื่อที่ต้องการ"""
    out = df.copy()

    # EMA / SMA
    out["close_10_ema"]  = EMAIndicator(close=out["Close"], window=ema_window).ema_indicator()
    out["close_50_sma"]  = SMAIndicator(close=out["Close"], window=sma50_window).sma_indicator()
    out["close_200_sma"] = SMAIndicator(close=out["Close"], window=sma200_window).sma_indicator()

    # MACD
    macd = MACD(close=out["Close"], window_slow=26, window_fast=12, window_sign=9)
    out["macd"]  = macd.macd()
    out["macds"] = macd.macd_signal()
    out["macdh"] = macd.macd_diff()

    # RSI
    out["rsi"] = RSIIndicator(close=out["Close"], window=rsi_window).rsi()

    # Bollinger Bands
    bb = BollingerBands(close=out["Close"], window=bb_window, window_dev=bb_dev)
    out["boll"]    = bb.bollinger_mavg()
    out["boll_ub"] = bb.bollinger_hband()
    out["boll_lb"] = bb.bollinger_lband()

    # ATR
    atr = AverageTrueRange(high=out["High"], low=out["Low"], close=out["Close"], window=atr_window)
    out["atr"] = atr.average_true_range()

    # VWMA = rolling sum(Close*Vol)/rolling sum(Vol)
    pv = (out["Close"] * out["Volume"]).rolling(window=vwma_window, min_periods=vwma_window).sum()
    vv = out["Volume"].rolling(window=vwma_window, min_periods=vwma_window).sum()
    out["vwma"] = pv / vv

    return out

def _last_row_to_dict(ind_df: pd.DataFrame) -> Dict[str, float]:
    last = ind_df.iloc[-1]
    out: Dict[str, float] = {}
    for key in REQUESTED_INDICATORS.keys():
        val = last.get(key, None)
        if pd.isna(val):
            continue
        out[key] = float(val)
    out["_last_bar_time_utc"] = ind_df.index[-1].strftime("%Y-%m-%d %H:%M:%S")
    return out

def _format_markdown_table(data: Dict[str, float]) -> str:
    """แปลง dict เป็นตาราง Markdown ตามลำดับ REQUESTED_INDICATORS"""
    lines = []
    lines.append("## INDICATORS (numeric)")
    if not data:
        lines.append("(no indicators)")
        lines.append("")
        return "\n".join(lines)

    lines.append("| Indicator | Value |")
    lines.append("|---|---|")
    for key, (display, _src) in REQUESTED_INDICATORS.items():
        if key not in data:
            continue
        v = data[key]
        val_str = f"{v:.4f}" if isinstance(v, (int, float)) else str(v)
        lines.append(f"| {display} | {val_str} |")
    lines.append("")
    return "\n".join(lines)

def get_yfin_indicators_dict(
    symbol: str,
    start_date: str,
    end_date: str,
    windows: Optional[Dict[str, float]] = None,
) -> Dict[str, float]:
    """
    อ่านราคาจาก CSV (ผ่าน get_YFin_data) → คำนวณอินดิเคเตอร์ → คืนค่า dict ของค่าล่าสุด
    windows: override เช่น {"ema":10,"sma50":50,"sma200":200,"rsi":14,"bb":20,"bb_dev":2.0,"atr":14,"vwma":20}
    """
    # ใช้ฟังก์ชันที่คุณมีอยู่แล้ว
    df = get_YFin_data(symbol, start_date, end_date)
    if df.empty:
        raise RuntimeError("No rows in requested date range.")

    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"], utc=True)
    df = df.set_index("Date")
    df = _normalize_ohlcv(df)
    df = _ensure_basic_columns(df)

    windows = windows or {}
    ind_df = _compute_indicators_yf(
        df,
        ema_window=int(windows.get("ema", 10)),
        sma50_window=int(windows.get("sma50", 50)),
        sma200_window=int(windows.get("sma200", 200)),
        rsi_window=int(windows.get("rsi", 14)),
        bb_window=int(windows.get("bb", 20)),
        bb_dev=float(windows.get("bb_dev", 2.0)),
        atr_window=int(windows.get("atr", 14)),
        vwma_window=int(windows.get("vwma", 20)),
    ).dropna()

    if ind_df.empty:
        raise RuntimeError("Not enough bars to compute indicators (dropna yielded empty). "
                           "Increase range or use smaller windows.")
    return _last_row_to_dict(ind_df)

def get_yfin_indicators(
    symbol: str,
    start_date: str,
    end_date: str,
    windows: Optional[Dict[str, float]] = None,
) -> str:
    """
    เวอร์ชัน “เหมือน TradingView” → คืน Markdown string
      - Header: symbol, date range, retrieved timestamp (UTC), last bar time
      - Body: ตาราง INDICATORS (numeric)
    """
    data = get_yfin_indicators_dict(symbol, start_date, end_date, windows=windows)
    last_bar = data.pop("_last_bar_time_utc", None)

    header  = f"# yfinance TA for {symbol.upper()} [{start_date} → {end_date}]\n"
    header += f"# Retrieved on: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
    if last_bar:
        header += f"# Last bar (UTC): {last_bar}\n\n"
    else:
        header += "\n"
    body = _format_markdown_table(data)
    return header + body

# -------- yfinance -------- #

def get_yfin_indicators_online_dict(
    symbol: str,
    period: str = "2y",
    interval: str = "1d",
    windows: Optional[Dict[str, float]] = None,
) -> Dict[str, float]:
    """
    ดาวน์โหลดจาก yfinance → คำนวณอินดิเคเตอร์ → คืน dict
    """
    df = yf.download(
        symbol,
        period=period,
        interval=interval,
        auto_adjust=False,
        progress=False,
        group_by="column",
        threads=True,
    )
    if df.empty:
        raise RuntimeError(f"No data for {symbol} (period={period}, interval={interval})")

    df.index = pd.to_datetime(df.index, utc=True)
    df = _normalize_ohlcv(df)
    df = _ensure_basic_columns(df)

    windows = windows or {}
    ind_df = _compute_indicators_yf(
        df,
        ema_window=int(windows.get("ema", 10)),
        sma50_window=int(windows.get("sma50", 50)),
        sma200_window=int(windows.get("sma200", 200)),
        rsi_window=int(windows.get("rsi", 14)),
        bb_window=int(windows.get("bb", 20)),
        bb_dev=float(windows.get("bb_dev", 2.0)),
        atr_window=int(windows.get("atr", 14)),
        vwma_window=int(windows.get("vwma", 20)),
    ).dropna()

    if ind_df.empty:
        raise RuntimeError("Not enough bars to compute indicators (dropna yielded empty). "
                           "Increase period or use smaller windows.")
    return _last_row_to_dict(ind_df)

def get_yfin_indicators_online(
    symbol: str,
    period: str = "2y",
    interval: str = "1d",
    windows: Optional[Dict[str, float]] = None,
) -> str:
    data = get_yfin_indicators_online_dict(symbol, period=period, interval=interval, windows=windows)
    last_bar = data.pop("_last_bar_time_utc", None)

    header  = f"# yfinance TA for {symbol.upper()} [{interval}] (period={period})\n"
    header += f"# Retrieved on: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
    if last_bar:
        header += f"# Last bar (UTC): {last_bar}\n\n"
    else:
        header += "\n"
    body = _format_markdown_table(data)
    return header + body


# ------------------------ twelve data  ------------------------ #

TD_BASE = "https://api.twelvedata.com"

def _td_get(path, params, api_key=None):
    api_key = "5fc2f7863f1c444987fd3b610db25220"
    if not api_key:
        raise RuntimeError("Set TWELVE_DATA_API_KEY")
    params = {**params, "apikey": api_key}
    r = requests.get(f"{TD_BASE}/{path}", params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    if "status" in data and data["status"] == "error":
        raise RuntimeError(f"TwelveData error: {data.get('message')}")
    return data

def get_twelve_data_indicator(symbol: str, interval="1day"):
    """
    ดึงเฉพาะค่าล่าสุดของชุดมาตรฐาน
    (ยิงทีละ endpoint ตามข้อจำกัด Twelve Data)
    """
    out = {}
    # SMA/EMA
    out["close_50_sma"]  = float(_td_get("sma", {"symbol":symbol,"interval":interval,"time_period":50})["values"][0]["sma"])
    out["close_200_sma"] = float(_td_get("sma", {"symbol":symbol,"interval":interval,"time_period":200})["values"][0]["sma"])
    out["close_10_ema"]  = float(_td_get("ema", {"symbol":symbol,"interval":interval,"time_period":10})["values"][0]["ema"])
    # MACD
    macd = _td_get("macd", {"symbol":symbol,"interval":interval,"fast":12,"slow":26,"signal":9})
    out["macd"]  = float(macd["values"][0]["macd"])
    out["macds"] = float(macd["values"][0]["macd_signal"])
    out["macdh"] = float(macd["values"][0]["macd_hist"])
    # RSI
    out["rsi"] = float(_td_get("rsi", {"symbol":symbol,"interval":interval,"time_period":14})["values"][0]["rsi"])
    # Bollinger
    bb = _td_get("bbands", {"symbol":symbol,"interval":interval,"time_period":20,"stddev":2})
    out["boll"]    = float(bb["values"][0]["middle_band"])
    out["boll_ub"] = float(bb["values"][0]["upper_band"])
    out["boll_lb"] = float(bb["values"][0]["lower_band"])
    # ATR
    out["atr"] = float(_td_get("atr", {"symbol":symbol,"interval":interval,"time_period":14})["values"][0]["atr"])
    # VWMA — ไม่มี endpoint ตรง ต้องคำนวณเองจาก time_series
    ts = _td_get("time_series", {"symbol":symbol,"interval":interval,"outputsize":60})
    import pandas as pd
    df = pd.DataFrame(ts["values"])
    df["close"]  = pd.to_numeric(df["close"], errors="coerce")
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
    vw = (df["close"]*df["volume"]).rolling(20).sum()/df["volume"].rolling(20).sum()
    out["vwma"] = float(vw.iloc[0])  # ค่าล่าสุดอยู่ index 0 ของ Twelve Data
    return out

# ===========================
# Compare only the fixed 6 indicators
# ===========================

COMPARE_KEYS = [
    "close_50_sma",   # 50 sma
    "close_200_sma",  # 200 sma
    "close_10_ema",   # 10 ema
    "macd",           # macd
    "macds",          # macd signal
    "macdh",          # macd histogram
    "rsi",            # rsi
    "boll",           # Bollinger middle band
    "boll_ub",        # Bollinger upper band
    "boll_lb",        # Bollinger lower band
    "atr",            # ATR
    "vwma",           # VWMA
]

# tolerance ต่ออินดิเคเตอร์ (จูนได้)
INDICATOR_TOL = {
    "rsi":            {"abs": 0.25, "rel": 0.0},
    "macd":           {"abs": 0.005, "rel": 0.0},
    "macds":          {"abs": 0.005, "rel": 0.0},
    "macdh":          {"abs": 0.005, "rel": 0.0},
    "close_10_ema":   {"abs": 0.03,  "rel": 6e-4},
    "close_50_sma":   {"abs": 0.04,  "rel": 6e-4},
    "close_200_sma":  {"abs": 0.06,  "rel": 6e-4},
    "boll":          {"abs": 0.05,  "rel": 7e-4},
    "boll_ub":        {"abs": 0.06,  "rel": 7e-4},
    "boll_lb":        {"abs": 0.06,  "rel": 7e-4},
    "atr":            {"abs": 0.05,  "rel": 7e-4},
    "vwma":           {"abs": 0.05,  "rel": 7e-4},
}

# ===========================
# Pick ONE source per indicator (prefer TV > YF > TD)
# ===========================

from typing import Optional

def _ensure_dir(path: str):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

def _save_json(obj, path: str):
    _ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def _append_jsonl_line(obj, path: str):
    _ensure_dir(path)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def _is_num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)

def _restrict(d: Optional[Dict]) -> Dict:
    """
    รับอะไรมาก็ตาม ถ้าไม่ใช่ dict → คืน {}
    ถ้าเป็น dict → คัดเหลือเฉพาะคีย์ที่อยู่ใน COMPARE_KEYS และแปลงเป็น float/None
    """
    if not isinstance(d, dict):
        return {}
    out = {}
    for k in COMPARE_KEYS:
        v = d.get(k, None)
        if _is_num(v):
            out[k] = float(v)
        else:
            out[k] = None
    return out

def _completeness(d: Dict, keys=COMPARE_KEYS) -> Tuple[int, int, float]:
    """
    คืน (นับคีย์ที่เป็นตัวเลข, นับคีย์ทั้งหมด, สัดส่วนความครบ)
    ถ้า d ไม่ใช่ dict ให้ถือว่าไม่มีข้อมูล
    """
    if not isinstance(d, dict):
        return 0, len(keys), 0.0
    n_tot = len(keys)
    n_num = sum(1 for k in keys if _is_num(d.get(k)))
    frac = (n_num / n_tot) if n_tot else 0.0
    return n_num, n_tot, frac

def _is_close_key(key: str, a: float, b: float, tol_cfg: dict) -> bool:
    cfg = tol_cfg.get(key, {"abs": 0.05, "rel": 1e-3})
    tol_abs, tol_rel = cfg["abs"], cfg["rel"]
    diff = abs(a - b)
    return diff <= max(tol_abs, tol_rel * max(abs(a), abs(b), 1e-12))

def _pair_agreement(a: Dict, b: Dict, keys=COMPARE_KEYS, tol_cfg=INDICATOR_TOL) -> Tuple[int, int, float]:
    """
    เปรียบเทียบสองแหล่ง: (hits, comps, score)
    - ถ้า a/b ไม่ใช่ dict ให้ถือว่าเทียบไม่ได้ (score=0)
    """
    if not isinstance(a, dict) or not isinstance(b, dict):
        return 0, 0, 0.0
    comps = 0
    hits = 0
    for k in keys:
        va, vb = a.get(k), b.get(k)
        if _is_num(va) and _is_num(vb):
            comps += 1
            if _is_close_key(k, float(va), float(vb), tol_cfg):
                hits += 1
    return hits, comps, (hits / comps if comps else 0.0)

def _consensus_scores(tv: Optional[Dict], yf: Optional[Dict], td: Optional[Dict]) -> Dict[str, Dict[str, float]]:
    """
    คำนวณคะแนน agreement ต่อแหล่ง (รองรับ input ที่ไม่ใช่ dict)
    """
    tv_r, yf_r, td_r = _restrict(tv), _restrict(yf), _restrict(td)
    present = {k: v for k, v in {"tradingview": tv_r, "yfinance": yf_r, "twelvedata": td_r}.items() if v}
    names = list(present.keys())
    scores = {name: {"hits": 0, "comps": 0, "score": 0.0} for name in names}

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            ni, nj = names[i], names[j]
            hi, ci, _ = _pair_agreement(present[ni], present[nj])
            scores[ni]["hits"]  += hi
            scores[ni]["comps"] += ci
            scores[nj]["hits"]  += hi
            scores[nj]["comps"] += ci

    for n in names:
        h, c = scores[n]["hits"], scores[n]["comps"]
        scores[n]["score"] = (h / c) if c else 0.0
    return scores

def choose_single_source_by_consensus(
    *,
    tv: Optional[dict] = None,
    yf: Optional[dict] = None,
    td: Optional[dict] = None,
) -> Dict:
    """
    เลือก 'เพียงแหล่งเดียว' ตามเกณฑ์:
      1) agreement สูงสุด
      2) completeness สูงสุด (tie-break)
      3) numeric_count สูงสุด (tie-break)
      4) ลำดับชื่อ (deterministic)
    """
    tv_r, yf_r, td_r = _restrict(tv), _restrict(yf), _restrict(td)
    present = {k: v for k, v in {"tradingview": tv_r, "yfinance": yf_r, "twelvedata": td_r}.items() if isinstance(v, dict) and v}

    if not present:
        raise RuntimeError("ไม่พบข้อมูลจากทุกแหล่ง")

    cons = _consensus_scores(tv_r, yf_r, td_r)

    for name, d in present.items():
        n_num, n_tot, frac = _completeness(d)
        cons.setdefault(name, {})
        cons[name]["completeness"] = frac
        cons[name]["numeric_count"] = n_num

    rank = sorted(
        present.keys(),
        key=lambda n: (
            cons.get(n, {}).get("score", 0.0),
            cons.get(n, {}).get("completeness", 0.0),
            cons.get(n, {}).get("numeric_count", 0),
            {"tradingview": 0, "yfinance": 1, "twelvedata": 2}.get(n, 9),
        ),
        reverse=True,
    )
    chosen = rank[0]
    final_payload = present[chosen]

    return {
        "chosen_source": chosen,
        "final_payload": final_payload,
        "scores": cons,
    }

# =========================
# Orchestrator: fetch → choose one source → save
# ใช้ตัวดึงเดิมของคุณ: get_tradingview_indicators_dict, get_yfin_indicators_online_dict, get_twelve_data_indicator
# =========================
def fetch_and_choose(symbol: str):
    """
    ดึงค่าจาก 3 แหล่ง (TV / yfinance / TwelveData) → เลือก 'แหล่งเดียว' จากเกณฑ์
      1) agreement สูงสุด
      2) completeness สูงสุด (tie-break)
      3) numeric_count สูงสุด (tie-break)
    จากนั้นบันทึกผลทั้งแบบ JSONL (summary) และ JSON (detail)

    return: Markdown ตารางสรุป (แสดง 'แหล่งเดียว' ที่เลือก + ค่า)
    """
    # ---------------- fetch ----------------
    tv_exchange: str = "NASDAQ"
    tv_screener: str = "america"
    tv_interval: str = "1d"
    yf_period: str = "2y"
    yf_interval: str = "1d"
    td_interval: str = "1day"

    sources = {}
    tv = yf = td = None

    try:
        tv = get_tradingview_indicators_dict(
            symbol, exchange=tv_exchange, screener=tv_screener, interval=tv_interval
        )
        if tv:
            sources["tradingview"] = tv
    except Exception:
        pass

    try:
        yf = get_yfin_indicators_online_dict(
            symbol, period=yf_period, interval=yf_interval
        )
        if yf:
            sources["yfinance"] = yf
    except Exception:
        pass

    try:
        td = get_twelve_data_indicator(symbol, interval=td_interval)
        if td:
            sources["twelvedata"] = td
    except Exception:
        pass

    if not sources:
        return {
            "error": "no_sources_available",
            "note": "ไม่สามารถดึงค่าจากทุกแหล่งได้ในตอนนี้",
        }

    # --------------- decide ONE source ---------------
    decision = choose_single_source_by_consensus(tv=tv, yf=yf, td=td)
    chosen = decision["chosen_source"]
    final_payload = decision["final_payload"]
    scores = decision["scores"]

    # --------------- save ---------------
    save_dir: str = f"data/indicators/{symbol.upper()}"
    jsonl_path: str = os.path.join(save_dir, "indicator_pick.jsonl")
    json_path:  str = os.path.join(save_dir, "indicator_pick_detail.json")

    now_iso = datetime.now(timezone.utc).isoformat()

    # summary JSONL (หนึ่งบรรทัดต่อการรัน)
    _append_jsonl_line({
        "timestamp": now_iso,
        "symbol": symbol.upper(),
        "chosen_source": chosen,
        "compare_keys": COMPARE_KEYS,
        "tolerance": INDICATOR_TOL,
        "scores": scores,
        "final_payload": final_payload,
        "available_sources": {
            "tradingview": bool(tv),
            "yfinance": bool(yf),
            "twelvedata": bool(td),
        }
    }, jsonl_path)

    # detail JSON
    _save_json({
        "timestamp": now_iso,
        "symbol": symbol.upper(),
        "chosen_source": chosen,
        "compare_keys": COMPARE_KEYS,
        "tolerance": INDICATOR_TOL,
        "scores": scores,
        "final_payload": final_payload,
        "raw": {
            "tradingview": tv or {},
            "yfinance": yf or {},
            "twelvedata": td or {},
        }
    }, json_path)

    # --------------- return (markdown สั้นอ่านง่าย) ---------------
    # แสดง “แหล่งเดียวที่เลือก” + ค่า
    title_map = {
        "close_50_sma":  "50 SMA",
        "close_200_sma": "200 SMA",
        "close_10_ema":  "10 EMA",
        "macd":          "MACD",
        "macds":         "MACD Signal",
        "macdh":         "MACD Histogram",
        "rsi":           "RSI",
        "boll":          "Bollinger Middle Band",
        "boll_ub":       "Bollinger Upper Band",
        "boll_lb":       "Bollinger Lower Band",
        "atr":           "ATR",
        "vwma":          "VWMA",
    }
    lines = []
    lines.append(f"# Indicator pick for {symbol.upper()} — **{chosen}**")
    lines.append("")
    lines.append("| Indicator | Value |")
    lines.append("|---|---|")
    for k in COMPARE_KEYS:
        v = final_payload.get(k)
        lines.append(f"| {title_map.get(k,k)} | {('-' if v is None else v)} |")
    lines.append("")
    return "\n".join(lines)


# ------------------------------ EDIT NEWS(GLOBAL) -----------------------------------------#
# ---------------- Finnhub News  -----------------
import finnhub

DEFAULT_API_KEY = os.getenv("FINNHUB_API_KEY", "d49dhs1r01qshn3lpbn0d49dhs1r01qshn3lpbng")

def _fh_client(api_key: Optional[str] = "d49dhs1r01qshn3lpbn0d49dhs1r01qshn3lpbng") -> finnhub.Client:
    key = api_key or DEFAULT_API_KEY
    if not key:
        raise RuntimeError("Missing FINNHUB_API_KEY")
    return finnhub.Client(api_key=key)

# ----------------- Small IO helpers -----------------
def _ensure_dir(path: str):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

def save_json(data, path: str):
    _ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_jsonl(items: List[Dict], path: str, append: bool = False):
    _ensure_dir(path)
    mode = "a" if append else "w"
    with open(path, mode, encoding="utf-8") as f:
        for obj in items:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

# ----------------- Time helpers -----------------
def _to_iso_or_raw(ts):
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    return ts

# ----------------- Field projection -----------------
WANTED_KEYS = {"datetime", "headline", "id", "source", "summary", "url"}

def project_fields(items: List[Dict]) -> List[Dict]:
    """เลือกเฉพาะฟิลด์สำคัญ + แปลง datetime เป็น ISO 8601"""
    out = []
    for it in items:
        obj = {k: it.get(k) for k in WANTED_KEYS}
        obj["datetime"] = _to_iso_or_raw(obj.get("datetime"))
        out.append(obj)
    return out

# ----------------- Core fetcher -----------------
def fetch_finnhub_world_news_raw(
    category: str = "general",
    *,
    max_pages: int = 3,
    sleep_s: float = 0.6,
) -> List[Dict]:
    """
    ดึงข่าว 'ทั่วไป/ข่าวโลก' จาก Finnhub แบบ RAW (ไม่ตัดฟิลด์)
    - ใช้การแบ่งหน้า (pagination) ด้วย min_id
    - category ที่นิยม: "general", "forex", "crypto", "merger"
    """
    api_key = "d49dhs1r01qshn3lpbn0d49dhs1r01qshn3lpbng"
    client = _fh_client(api_key)
    all_items: List[Dict] = []
    min_id = 0
    for _ in range(max_pages):
        batch = client.general_news(category, min_id=min_id)
        if not batch:
            break
        all_items.extend(batch)
        # min_id ถัดไป = id ของรายการสุดท้ายในหน้าปัจจุบัน
        min_id = batch[-1].get("id", min_id)
        time.sleep(sleep_s)
    return all_items

def fetch_finnhub_world_news() -> List[Dict]:
    """
    ดึงข่าวโลกจาก Finnhub แล้ว (ค่าเริ่มต้น):
      - คัดเฉพาะฟิลด์ที่ต้องใช้ (datetime/headline/id/source/summary/url) + datetime → ISO
      - ถ้าต้องการ RAW ให้ตั้ง return_raw=True
      - รองรับการเซฟ JSON/JSONL (ถ้าระบุ path)

    Return: List[Dict] (raw หรือ slim ตาม return_raw)
    """
    
    category: str = "general"
    max_pages: int = 3
    sleep_s: float = 0.6
    return_raw: bool = False
    save_jsonl_path: Optional[str] = f"data/global_news/finnhub_world_news.jsonl"  # เช่น "./data/news/world/finnhub_general_news.slim.jsonl"
    api_key = "d49dhs1r01qshn3lpbn0d49dhs1r01qshn3lpbng"
    raw_items = fetch_finnhub_world_news_raw(
        category=category, max_pages=max_pages, sleep_s=sleep_s
    )

    if return_raw:
        if save_jsonl_path:
            save_jsonl(raw_items, save_jsonl_path, append=False)
        return raw_items

    # slim (เลือกฟิลด์/แปลงเวลา)
    slim = project_fields(raw_items)

    # เซฟ (slim) ถ้าระบุ path
    if save_jsonl_path:
        save_jsonl(slim, save_jsonl_path, append=False)

    return slim
    
# ------------------------------ EDIT NEWS GLOBAL(REDDIT) -----------------------------------------#
    
from typing import Iterable, List, Dict, Optional
import praw


DEFAULT_SUBS = ["worldnews", "news", "business", "economics"]


# ---------------------------
# Client / IO Utilities
# ---------------------------

def make_reddit_client(
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    user_agent: Optional[str] = None,
    ratelimit_seconds: int = 5,
) -> praw.Reddit:
    """
    สร้าง PRAW client แบบ read-only
    ค่าเริ่มต้นอ่านจาก ENV:
      REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT
    """
    client_id = "6ntwQ2TEM4UZNlsjqO9T0A"
    client_secret = "GaSCQu0ZMPwLr-zfs9PBFFfVPKrncg"
    user_agent = os.getenv("REDDIT_USER_AGENT", "news-fetcher:v1 (by u/yourname)")

    if not client_id or not user_agent:
        raise RuntimeError("กรุณาตั้ง ENV/พารามิเตอร์: REDDIT_CLIENT_ID และ REDDIT_USER_AGENT (REDDIT_CLIENT_SECRET ใส่หรือไม่ก็ได้)")

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret or None,  # บางแอปแบบ installed สามารถเว้นได้
        user_agent=user_agent,
        ratelimit_seconds=ratelimit_seconds,
    )
    reddit.read_only = True
    return reddit

def _ts_to_iso(ts: float | int | None) -> Optional[str]:
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat()
    except Exception:
        return None


def _normalize_post(p) -> Dict:
    """ดึงฟิลด์สำคัญ + แปลงเวลาเป็น ISO"""
    return {
        "id": p.id,
        "subreddit": str(getattr(p, "subreddit", "")),
        "title": p.title,
        "url": p.url,
        "permalink": f"https://reddit.com{p.permalink}",
        "flair": getattr(p, "link_flair_text", None),
        "created_utc": float(getattr(p, "created_utc", 0.0)) if getattr(p, "created_utc", None) is not None else None,
        "created_iso": _ts_to_iso(getattr(p, "created_utc", None)),
        "selftext": (getattr(p, "selftext", "") or "").strip(),
        "score": int(getattr(p, "score", 0)),
        "num_comments": int(getattr(p, "num_comments", 0)),
        "over_18": bool(getattr(p, "over_18", False)),
        "author": str(getattr(getattr(p, "author", None), "name", "") or ""),
    }


def fetch_subreddit_top(
    reddit: praw.Reddit,
    sub: str,
    *,
    time_filter: str = "day",   # "hour" | "day" | "week" | "month" | "year" | "all"
    limit: int = 20,
    skip_nsfw: bool = True,
    sleep_per_item: float = 0.05,
) -> List[Dict]:
    """
    ดึงโพสต์ Top ตามช่วงเวลาที่กำหนดของ subreddit หนึ่ง
    คืนรายการที่ถูก normalize แล้ว (dict)
    """
    out: List[Dict] = []
    try:
        for p in reddit.subreddit(sub).top(time_filter=time_filter, limit=limit):
            if skip_nsfw and bool(getattr(p, "over_18", False)):
                continue
            out.append(_normalize_post(p))
            if sleep_per_item:
                time.sleep(sleep_per_item)  # ถี่มากไปอาจโดน 429
    except Exception as e:
        print(f"[WARN] r/{sub} error: {e}")
    return out


def fetch_multi_subs_top(
    reddit: praw.Reddit,
    subs: Iterable[str] = DEFAULT_SUBS,
    *,
    time_filter: str = "day",
    per_sub_limit: int = 20,
    dedupe: bool = True,
    sort_by_score_desc: bool = True,
) -> List[Dict]:
    """
    ดึงรวมหลาย subreddit แล้ว (option) ลบโพสต์ซ้ำด้วย id และเรียงตาม score
    """
    all_posts: List[Dict] = []
    seen: set[str] = set()

    for s in subs:
        batch = fetch_subreddit_top(
            reddit, s, time_filter=time_filter, limit=per_sub_limit
        )
        if not dedupe:
            all_posts.extend(batch)
            continue

        for it in batch:
            pid = it.get("id")
            if not pid or pid in seen:
                continue
            seen.add(pid)
            all_posts.append(it)

    if sort_by_score_desc:
        all_posts.sort(key=lambda x: (x.get("score") or 0), reverse=True)

    return all_posts


def fetch_world_news_today(
    subs: Iterable[str] = DEFAULT_SUBS,
    *,
    per_sub_limit: int = 20,
    time_filter: str = "day",
    client: Optional[praw.Reddit] = None,
) -> List[Dict]:
    """
    ดึง Top วันนี้ (หรือช่วงอื่นตาม time_filter) จากหลาย subs ที่กำหนด
    """
    reddit = client or make_reddit_client()
    return fetch_multi_subs_top(
        reddit,
        subs=subs,
        time_filter=time_filter,
        per_sub_limit=per_sub_limit,
        dedupe=True,
        sort_by_score_desc=True,
    )


def fetch_reddit_world_news() -> str:
    """
    ดึง → รวม → เซฟเป็นไฟล์ (JSONL เป็นค่าเริ่มต้น)
    คืน path ของไฟล์ที่บันทึก
    """
    out_path: str = "data/global_news/reddit_world_news.jsonl"
    subs: Iterable[str] = DEFAULT_SUBS
    per_sub_limit: int = 20
    time_filter: str = "week"
    jsonl: bool = True
    posts = fetch_world_news_today(
        subs=subs,
        per_sub_limit=per_sub_limit,
        time_filter=time_filter,
    )
    if jsonl:
        save_jsonl(posts, out_path, append=False)
    else:
        # เผื่ออยากดูทีเดียวทั้งไฟล์
        save_json(posts, out_path)
    return out_path

# ------------------------------ EDIT NEWS GLOBAL(YFINANCE) -----------------------------------------#

from datetime import datetime, timedelta, timezone
from yfinance import Search

def _to_epoch(dt: datetime) -> int:
    return int(dt.replace(tzinfo=timezone.utc).timestamp())

def _ensure_dir(path: str):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

def _save_json(items: List[Dict], path: str):
    _ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

def _save_jsonl(items: List[Dict], path: str, append: bool = False):
    _ensure_dir(path)
    mode = "a" if append else "w"
    with open(path, mode, encoding="utf-8") as f:
        for obj in items:
            f.write(json.dumps(obj, ensure_ascii=False))
            f.write("\n")

def _window_epochs(curr_date: str, look_back_days: int) -> Tuple[int, int]:
    """คืน (start_epoch, end_epoch) โดยครอบทั้งวันของช่วงเวลา"""
    curr_dt  = datetime.strptime(curr_date, "%Y-%m-%d")
    start_dt = (curr_dt - timedelta(days=look_back_days)).replace(hour=0, minute=0, second=0, microsecond=0)
    end_dt   = curr_dt.replace(hour=23, minute=59, second=59, microsecond=0)
    return _to_epoch(start_dt), _to_epoch(end_dt)

_YF_KEEP = {
    "title", "link", "publisher", "providerPublishTime",
    "type", "uuid", "relatedTickers", "thumbnail"
}

def _normalize_item(n: Dict) -> Dict:
    """คงฟิลด์สำคัญ + เพิ่ม iso & date_str เพื่อใช้งาน/แสดงผลสะดวก"""
    out = {k: n.get(k) for k in _YF_KEEP}
    ts = n.get("providerPublishTime")
    if isinstance(ts, (int, float)):
        dt = datetime.fromtimestamp(int(ts), tz=timezone.utc)
        out["published_iso"] = dt.isoformat()
        out["published_date"] = dt.strftime("%Y-%m-%d")
    else:
        out["published_iso"] = None
        out["published_date"] = None
    # บางรายการไม่มี uuid → ใช้ลิงก์ช่วย dedupe
    out["_dedup_key"] = str(out.get("uuid") or out.get("link") or "")
    return out


# ---------------------------
# Fetchers
# ---------------------------

def search_yf_news(keyword: str, *, news_count: int = 40) -> List[Dict]:
    """
    ดึงข่าวจาก yfinance.Search ต่อคีย์เวิร์ดเดียว
    คืนรายการดิบ (ยังไม่ normalize/กรองเวลา)
    """
    try:
        s = Search(keyword, news_count=news_count)
        return list(getattr(s, "news", []) or [])
    except Exception:
        return []

def fetch_yf_news_by_keywords(
    keywords: Iterable[str],
    *,
    start_epoch: Optional[int] = None,
    end_epoch: Optional[int] = None,
    per_keyword: int = 40,
    limit_total: int = 50,
) -> List[Dict]:
    """
    ดึงข่าวหลายคีย์เวิร์ด → รวม → ลบซ้ำ → กรองตามช่วงเวลา → เรียงเวลาล่าสุดก่อน → ตัดตาม limit_total
    คืนรายการที่ถูก normalize แล้ว
    """
    seen: set[str] = set()
    kept: List[Dict] = []

    for kw in keywords:
        raw = search_yf_news(kw, news_count=per_keyword)
        for n in raw:
            item = _normalize_item(n)
            dedup = item.get("_dedup_key", "")
            if not dedup or dedup in seen:
                continue
            ts = n.get("providerPublishTime")
            if isinstance(ts, (int, float)) and start_epoch is not None and end_epoch is not None:
                if not (start_epoch <= int(ts) <= end_epoch):
                    continue
            elif not isinstance(ts, (int, float)):
                # ถ้าไม่มีเวลาเผยแพร่ ข้ามเพื่อให้หน้าต่างเวลามีความหมาย
                continue
            seen.add(dedup)
            kept.append(item)

    # เรียงเวลาใหม่สุดก่อน
    kept.sort(key=lambda x: x.get("providerPublishTime", 0), reverse=True)
    return kept[:limit_total]


# ---------------------------
# Orchestrator (World News)
# ---------------------------

DEFAULT_WORLD_KEYWORDS = [
    "world", "world news", "geopolitics", "global economy", "international"
]

def get_world_news_yf() -> List[Dict]:
    """
    ดึง 'ข่าวโลก' ด้วย yfinance (ค้นหลายคีย์เวิร์ดทั่วไป):
      1) นิยามหน้าต่างเวลา [curr_date - look_back_days, curr_date]
      2) ดึงข่าวจากหลายคีย์เวิร์ด
      3) รวม/ลบซ้ำ/กรองวัน/เรียง → ตัดตาม limit
      4) (ออปชัน) เซฟ JSON/JSONL

    return: list[dict] ที่ normalize แล้ว
    """
    curr_date: str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    look_back_days: int = 7
    limit: int = 50
    keywords: Optional[Iterable[str]] = None
    per_keyword: Optional[int] = None
    save_jsonl_path: Optional[str] = "data/global_news/yfinance_world_news.jsonl"
    start_epoch, end_epoch = _window_epochs(curr_date, look_back_days)
    kw = list(keywords) if keywords else DEFAULT_WORLD_KEYWORDS

    # 1) สร้างช่วงเวลา
    start_epoch, end_epoch = _window_epochs(curr_date, look_back_days)

    # 2) กำหนดคีย์เวิร์ด
    kw = list(keywords) if keywords else DEFAULT_WORLD_KEYWORDS

    # 3) เผื่อดึงเกินมาเพื่อดีดซ้ำออก
    if per_keyword is None:
        per_keyword = max(10, min(100, (limit // max(1, len(kw))) * 2 or 20))

    # 4) ดึงข่าวดิบจาก yfinance (ผลลัพธ์ดิบจะมีฟิลด์เช่น: uuid, title, link, publisher, providerPublishTime)
    raw_items = fetch_yf_news_by_keywords(
        kw,
        start_epoch=start_epoch,
        end_epoch=end_epoch,
        per_keyword=per_keyword,
        limit_total=limit,
    )

    # 5) map ให้เหลือ 5 ฟิลด์ตามต้องการ
    normalized: List[Dict] = []
    seen = set()
    for n in raw_items:
        # ใช้ uuid เป็นตัวลบซ้ำหลัก; ถ้าไม่มีให้ fallback เป็น link
        dedup = n.get("uuid") or n.get("link")
        if not dedup or dedup in seen:
            continue
        seen.add(dedup)

        normalized.append({
            "uuid":           n.get("uuid") or "",
            "publisher":      n.get("publisher") or "",
            "title":          n.get("title") or "",
            "link":           n.get("link") or "",
            "published_date": _epoch_to_iso(n.get("providerPublishTime")),
        })

    # 6) (ออปชัน) บันทึก JSONL
    if save_jsonl_path:
        os.makedirs(os.path.dirname(save_jsonl_path) or ".", exist_ok=True)
        _save_jsonl(normalized, save_jsonl_path, append=False)

    return normalized

# ------------------------------ EDIT NEWS(PER_STOCK) -----------------------------------------#
# --------------------------- finnhub ------------------------#
import os, json
from datetime import datetime, timedelta, timezone
import finnhub
import yfinance as yf


def _ensure_dir(path: str):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

def save_json(items: List[Dict], path: str):
    _ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

def save_jsonl(items: List[Dict], path: str, append: bool = False):
    _ensure_dir(path)
    mode = "a" if append else "w"
    with open(path, mode, encoding="utf-8") as f:
        for obj in items:
            f.write(json.dumps(obj, ensure_ascii=False))
            f.write("\n")

def _to_epoch(dt: datetime) -> int:
    return int(dt.replace(tzinfo=timezone.utc).timestamp())

def _window_epochs(curr_date: str, look_back_days: int) -> Tuple[int, int]:
    curr_dt  = datetime.strptime(curr_date, "%Y-%m-%d")
    start_dt = (curr_dt - timedelta(days=look_back_days)).replace(hour=0, minute=0, second=0, microsecond=0)
    end_dt   = curr_dt.replace(hour=23, minute=59, second=59, microsecond=0)
    return _to_epoch(start_dt), _to_epoch(end_dt)

def _epoch_to_iso(ts: int | float | None) -> Optional[str]:
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()
    return None

def _norm_finnhub_item(symbol: str, it: Dict) -> Dict:
    ts = it.get("datetime")
    iso = _epoch_to_iso(ts)
    date_str = iso[:10] if iso else None
    return {
        "source": "finnhub",
        "symbol": symbol.upper(),
        "title": it.get("headline"),
        "summary": it.get("summary"),
        "publisher": it.get("source"),
        "url": it.get("url"),
        "published_epoch": int(ts) if isinstance(ts, (int, float)) else None,
        "published_iso": iso,
        "published_date": date_str,
        "raw": it,
        "_dedup_key": str(it.get("id") or it.get("url") or ""),
    }

def _norm_yf_item(symbol: str, it: Dict) -> Dict:
    ts = it.get("providerPublishTime")
    iso = _epoch_to_iso(ts)
    date_str = iso[:10] if iso else None
    # yfinance.Ticker(symbol).news: keys: title, link, publisher, providerPublishTime, type, uuid, ...
    return {
        "source": "yfinance",
        "symbol": symbol.upper(),
        "title": it.get("title"),
        "summary": None,  # YF ข่าวบริษัทส่วนใหญ่ไม่มี summary ตรงๆ
        "publisher": it.get("publisher"),
        "url": it.get("link"),
        "published_epoch": int(ts) if isinstance(ts, (int, float)) else None,
        "published_iso": iso,
        "published_date": date_str,
        "raw": it,
        "_dedup_key": str(it.get("uuid") or it.get("link") or ""),
    }


def fetch_company_news_finnhub(
    symbol: str,
    start_date: str,   # "YYYY-MM-DD"
    end_date: str,     # "YYYY-MM-DD"
    *,
    api_key: Optional[str] = None,
    client: Optional[finnhub.Client] = None,
) -> List[Dict]:
    """
    ดึงข่าวบริษัท (Finnhub) ตามช่วงวัน (ชั้นข้อมูลฟรีย้อนหลัง~1ปี)
    """
    if client is None:
        api_key = "d49dhs1r01qshn3lpbn0d49dhs1r01qshn3lpbng"
        if not api_key:
            raise RuntimeError("Missing FINNHUB_API_KEY")
        client = finnhub.Client(api_key=api_key)

    raw = client.company_news(symbol.upper(), _from=start_date, to=end_date) or []
    out = []
    seen = set()
    for it in raw:
        n = _norm_finnhub_item(symbol, it)
        if not n["_dedup_key"] or n["_dedup_key"] in seen:
            continue
        seen.add(n["_dedup_key"])
        # กันข่าวที่ไม่มี timestamp
        if n["published_epoch"] is None:
            continue
        out.append(n)
    return out

# def fetch_company_news_yfinance(
#     symbol: str,
#     *,
#     look_back_days: Optional[str] = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d"),
#     curr_date: Optional[str] = datetime.now(timezone.utc).strftime("%Y-%m-%d"),    # ใช้คู่กับ look_back_days
# ) -> List[Dict]:
#     """
#     ดึงข่าวบริษัทจาก yfinance.Ticker(symbol).news
#     - ถ้าระบุ curr_date + look_back_days จะกรองตามหน้าต่างเวลา
#     """
#     tkr = yf.Ticker(symbol)
#     raw = getattr(tkr, "news", []) or []
#     out = []
#     seen = set()

#     # กำหนดหน้าต่างเวลา (optional)
#     if curr_date and look_back_days is not None:
#         start_ep, end_ep = _window_epochs(curr_date, look_back_days)
#     else:
#         start_ep = end_ep = None

#     for it in raw:
#         n = _norm_yf_item(symbol, it)
#         if not n["_dedup_key"] or n["_dedup_key"] in seen:
#             continue
#         if n["published_epoch"] is None:
#             continue
#         if start_ep is not None and end_ep is not None:
#             if not (start_ep <= n["published_epoch"] <= end_ep):
#                 continue
#         seen.add(n["_dedup_key"])
#         out.append(n)
#     return out

# ---------------------------
# Merge & Orchestrator
# ---------------------------

def merge_company_news(
    *lists: Iterable[Dict],
    limit: int = 100
) -> List[Dict]:
    """
    รวมข่าวจากหลายแหล่ง, ลบโพสต์ซ้ำตาม _dedup_key, เรียงเวลาล่าสุดก่อน แล้วตัดตาม limit
    """
    merged: List[Dict] = []
    seen = set()
    for lst in lists:
        for n in lst:
            dk = n.get("_dedup_key") or ""
            if not dk or dk in seen:
                continue
            seen.add(dk)
            merged.append(n)
    merged.sort(key=lambda x: (x.get("published_epoch") or 0), reverse=True)
    return merged[:limit]

def finnhub_get_company_news( symbol: str ) -> List[Dict]:
    """
    Orchestrator: ดึงข่าวบริษัทจาก Finnhub + yfinance → รวม/ลบซ้ำ/เรียง/ตัด
    - อย่างน้อยควรส่งช่วงวันสำหรับ Finnhub (start_date/end_date)
    - ถ้าอยากกรอง yfinance ด้วย ก็ส่ง curr_date + look_back_days เพิ่ม
    """
    # Finnhub window
    start_date: Optional[str] = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    end_date: Optional[str] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # runtime
    limit: int = 50
    save_jsonl_path: Optional[str] = f"data/stock/{symbol}/finnhub_company_news.jsonl"
    items_fh: List[Dict] = []
    items_yf: List[Dict] = []
    finnhub_api_key = "d49dhs1r01qshn3lpbn0d49dhs1r01qshn3lpbng"

    if start_date and end_date:
        try:
            items_fh = fetch_company_news_finnhub(
                symbol, start_date, end_date, api_key=finnhub_api_key
            )
        except Exception:
            # ไม่ล้มทั้งงาน หาก Finnhub มีปัญหา
            items_fh = []

    merged = merge_company_news(items_fh, items_yf, limit=limit)
    reportmessage = f"📰 News :\n" \
                    f"Fetched {len(merged)} news items for {symbol} from Finnhub." 

    # write text file
    with open("all_report_message.txt", "a", encoding='utf-8') as file:
        file.write(reportmessage + "\n")

    # ถ้าผู้เรียกส่ง save_jsonl_path ให้เติม {symbol} แล้วสร้างไดเรกทอรีถ้ายังไม่มี
    if save_jsonl_path:
        try:
            path = save_jsonl_path.format(symbol=symbol)
        except Exception:
            path = save_jsonl_path  # ถ้าไม่มี placeholder หรือ format ผิด ให้ใช้ตรงๆ
        dirpath = os.path.dirname(path) or "."
        os.makedirs(dirpath, exist_ok=True)
        save_jsonl(merged, path, append=False)

    return merged

# ------------------------------ news stock subreddit -----------------------------------------#
from datetime import datetime, timedelta, timezone

REDDIT_TOKEN_URL  = "https://www.reddit.com/api/v1/access_token"
REDDIT_OAUTH_BASE = "https://oauth.reddit.com"

CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "6ntwQ2TEM4UZNlsjqO9T0A")
CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "GaSCQu0ZMPwLr-zfs9PBFFfVPKrncg")
USER_AGENT = "news-fetcher:v1 (by u/keingkrai)"

# ---------- small io helpers ----------
def _ensure_parent_dir(path: str):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

def save_jsonl(items, path, append: bool = False):
    _ensure_parent_dir(path)
    mode = "a" if append else "w"
    with open(path, mode, encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

def _slug(s: str) -> str:
    """ทำให้เป็นชื่อไฟล์/โฟลเดอร์ที่ปลอดภัยขึ้น"""
    if s is None:
        return "all"
    s = s.strip()
    s = re.sub(r"[\\/:*?\"<>|]+", "_", s)   # แทนที่อักขระต้องห้ามบน Windows
    s = re.sub(r"\s+", "_", s)              # เว้นวรรคเป็น _
    return s[:120] or "all"                 # limit ความยาวกันยาวเกิน

# ---------- reddit auth ----------
def get_token():
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    auth = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
    r = s.post(REDDIT_TOKEN_URL, auth=auth, data={"grant_type": "client_credentials"}, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]

# ---------- main search ----------
def reddit_get_company_news(query: str):
    """
    ค้นใน subreddit เดียวด้วย restrict_sr + sort=top (เวอร์ชันเรียบง่าย)
    - ถ้าไม่ส่ง save_path → จะสร้าง path อัตโนมัติ: data\stock\<query>\reddit_search_<sub>_<YYYYMMDD>_<YYYYMMDD>.jsonl
    - สร้างโฟลเดอร์ปลายทางให้เสมอ
    """
    sub: str = "news"
    start_dt: datetime = datetime.now(tz=timezone.utc) - timedelta(days=30)
    end_dt: datetime   = datetime.now(tz=timezone.utc)
    limit: int = 50
    save_path: str | None = None
    token = get_token()
    s = requests.Session()
    s.headers.update({
        "Authorization": f"bearer {token}",
        "User-Agent": USER_AGENT
    })

    # --------- สร้าง path ปลายทางอัตโนมัติ ถ้าไม่ส่งมา ----------
    if save_path is None:
        qslug = _slug(query)
        start_str = start_dt.astimezone(timezone.utc).strftime("%Y%m%d")
        end_str   = end_dt.astimezone(timezone.utc).strftime("%Y%m%d")
        save_path = f"data/stock/{qslug}/reddit_company_news_{end_str}.jsonl"

    url = f"{REDDIT_OAUTH_BASE}/r/{sub}/search.json"
    params = {
        "q": f"{query or ''}",
        "syntax": "cloudsearch",
        "restrict_sr": "true",
        "sort": "top",
        "limit": str(min(limit, 100)),
    }

    # ยิงพร้อม retry เล็กน้อยกัน 429/5xx
    for attempt in range(3):
        r = s.get(url, params=params, timeout=30)
        if r.status_code == 429:
            time.sleep(2 + attempt)
            continue
        r.raise_for_status()
        break

    out = []
    data = r.json().get("data", {}) or {}
    for ch in data.get("children", []) or []:
        d = ch.get("data", {}) or {}
        if d.get("over_18", False):
            continue
        out.append({
            "id": d.get("id"),
            "title": d.get("title", ""),
            "url": d.get("url", ""),
            "permalink": "https://reddit.com" + (d.get("permalink") or ""),
            "created_utc": d.get("created_utc", 0),
            "selftext": (d.get("selftext") or "").strip(),
            "flair": d.get("link_flair_text"),
            "subreddit": d.get("subreddit"),
            "score": d.get("score"),
            "num_comments": d.get("num_comments"),
        })
        time.sleep(0.05)

    # เซฟ (สร้างโฟลเดอร์ให้แน่ใจ)
    if save_path:
        save_jsonl(out, save_path, append=False)

    print(f"Fetched {len(out)} posts from r/{sub} for query='{query}' -> {save_path}")

    # write text file
    reportmessage = f"Fetched {len(out)} news items for {query} from Reddit."

    with open("all_report_message.txt", "a") as file:
        file.write(reportmessage + "\n")

    return out

# ------------------------------ news stock yfinance -----------------------------------------#
import yfinance as yf

def _ensure_dir(path: str):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

def _save_json(items: List[Dict], path: str):
    _ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

def _save_jsonl(items: List[Dict], path: str, append: bool = False):
    _ensure_dir(path)
    mode = "a" if append else "w"
    with open(path, mode, encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

def yfinance_get_company_news(symbol: str) -> List[Dict]:
    """
    ดึงข่าว 'ดิบ' จาก yfinance ตามที่ได้จาก API ตรง ๆ (ไม่กรองเวลา, ไม่ลบซ้ำ, ไม่เปลี่ยนฟิลด์)
    จำกัดรายการไม่เกิน max_items (default 50)
    - ใส่แค่ symbol อย่างเดียว
    - เซฟไฟล์อัตโนมัติไว้ที่ ./data/stock/<symbol>/:
        - yfinance_company_news_<YYYY-MM-DD>.json
        - yfinance_company_news_<YYYY-MM-DD>.jsonl
    - คืนค่าลิสต์ข่าวแบบ raw ตาม yfinance (ถูกตัดให้ไม่เกิน max_items)
    """
    max_items: int = 50
    t = yf.Ticker(symbol)
    try:
        news = t.get_news()            # บางเวอร์ชันของ yfinance
    except Exception:
        news = getattr(t, "news", []) or []

    # coerce ให้เป็น list (ถ้าไม่ใช่)
    if not isinstance(news, list):
        try:
            news = list(news)
        except Exception:
            news = [news]

    # จำกัดจำนวนข่าวไม่เกิน max_items
    news = news[:max_items]

    # เซฟแบบ raw ทั้งหมด (ทั้ง .json และ .jsonl)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    json_path = f"data/stock/{symbol}/yfinance_company_news_{today}.json"
    jsonl_path = f"data/stock/{symbol}/yfinance_company_news_{today}.jsonl"

    try:
        _save_json(news, json_path)
    except Exception:
        # ถ้าไม่มี helper นี้ หรือเซฟไม่สำเร็จ ก็ข้าม
        pass

    try:
        _save_jsonl(news, jsonl_path, append=False)
    except Exception:
        pass

    # write text file
    reportmessage = f"Fetched {len(news)} news items for {symbol} from YFinance."
    with open("all_report_message.txt", "a") as file:
        file.write(reportmessage + "\n")

    return news

# ------------------------------ Alpha vatantage news stock -----------------------------------------#
def alphavantage_get_company_news(
    symbol: str
) -> List[Dict]:
    """
    ดึง 'ข่าวดิบ' ของบริษัทด้วย Alpha Vantage NEWS_SENTIMENT
    - ใส่แค่ symbol (e.g., 'AAPL')
    - จำกัดผลลัพธ์ไม่เกิน max_items (default 50)
    - เซฟไฟล์อัตโนมัติ: ./data/stock/<symbol>/
        - alphavantage_company_news_<YYYY-MM-DD>.json
        - alphavantage_company_news_<YYYY-MM-DD>.jsonl
    - คืนค่าลิสต์ข่าวแบบ raw ตาม Alpha Vantage (ถูกตัดจำนวนรายการ)
    หมายเหตุ:
    - ต้องตั้งค่า ALPHAVANTAGE_API_KEY ใน env หรือส่ง api_key เข้ามา
    - NEWS_SENTIMENT รองรับตัวกรองเวลาแบบ time_from/time_to ในรูป YYYYMMDDTHHMM
    """
    look_back_days: int = 7
    max_items: int = 50
    base_url = "https://www.alphavantage.co/query"
    api_key = "7DJF0DNKIR9T1F9X"
    if not api_key:
        raise ValueError("Missing ALPHAVANTAGE_API_KEY. Set env or pass api_key param.")

    # สร้างช่วงเวลา (UTC) ย้อนหลัง look_back_days วัน
    end_dt = datetime.now(timezone.utc)
    start_dt = end_dt - timedelta(days=look_back_days)
    # รูปแบบเวลาตาม Alpha Vantage: YYYYMMDDTHHMM
    tf = start_dt.strftime("%Y%m%dT%H%M")
    tt = end_dt.strftime("%Y%m%dT%H%M")

    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": symbol.upper(),
        "time_from": tf,
        "time_to": tt,
        "sort": "LATEST",        # หรือ "EARLIEST"
        "limit": str(max(10, min(max_items, 100))),  # AV จำกัดสูงสุด ~100 ต่อคำขอ
        "apikey": api_key,
    }

    # เรียก API พร้อม retry ง่ายๆ กันเคส 5xx/429
    session = requests.Session()
    items = []
    for attempt in range(3):
        try:
            r = session.get(base_url, params=params, timeout=30)
            if r.status_code in (429, 503):
                time.sleep(2 + attempt)
                continue
            r.raise_for_status()
            data = r.json() or {}

            # Alpha Vantage อาจส่งฟิลด์ "Note" เมื่อติด rate limit
            if "Note" in data:
                # รอแล้วลองใหม่
                time.sleep(5 + attempt * 2)
                continue

            # ข่าวอยู่ใน key "feed"
            feed = data.get("feed", []) or []
            if not isinstance(feed, list):
                try:
                    feed = list(feed)
                except Exception:
                    feed = [feed]

            items = feed[:max_items]
            break
        except requests.HTTPError:
            if attempt == 2:
                raise
            time.sleep(2 + attempt)
        except Exception:
            if attempt == 2:
                raise
            time.sleep(1 + attempt)

    # เซฟผลลัพธ์แบบ raw
    today = end_dt.strftime("%Y-%m-%d")
    jsonl_path = f"data/stock/{symbol}/alphavantage_company_news_{today}.jsonl"

    try:
        _save_jsonl(items, jsonl_path, append=False)
    except Exception:
        pass

    # write text file
    reportmessage = f"Fetched {len(items)} news items for {symbol} from Alpha Vantage."
    with open("all_report_message.txt", "a") as file:
        file.write(reportmessage + "\n")

    return items
# ------------------------------ EDIT SOCIAL MEDIA ---------------------------------#
# ------------------------------  BlueSky  ---------------------------------#
from atproto import Client, models as atp_models

# =============================== IO helpers ===============================

def _ensure_dir(path: str):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

def save_jsonl(items: List[Dict], path: str, append: bool = False):
    _ensure_dir(path)
    mode = "a" if append else "w"
    with open(path, mode, encoding="utf-8") as f:
        for obj in items:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

# =============================== Bluesky core ==============================

def _post_url_from_uri(uri: str, handle: str) -> str:
    rkey = uri.split("/")[-1]
    return f"https://bsky.app/profile/{handle}/post/{rkey}"

def _collect_query(
    client: Client,
    q: str,
    limit_total: int,
    *,
    cursor: Optional[str] = None,
    sleep_s: float = 0.05,
    max_pages: int = 200,
) -> List[Dict]:
    """
    ดึงผลค้นหาแบบแบ่งหน้า (search_posts) จนครบ limit_total หรือหมดหน้า
    คืน list ของโพสต์ที่ normalize ฟิลด์สำคัญแล้ว
    """
    out: List[Dict] = []
    pages = 0
    while len(out) < limit_total and pages < max_pages:
        params = atp_models.AppBskyFeedSearchPosts.Params(
            q=q,
            limit=min(100, limit_total - len(out)),
            cursor=cursor,
        )
        res = client.app.bsky.feed.search_posts(params=params)

        posts = res.posts or []
        for p in posts:
            author = p.author
            handle = getattr(author, "handle", "") or getattr(author, "did", "")
            display = getattr(author, "display_name", None) or handle
            record = p.record  # has .text, .created_at
            uri = p.uri
            out.append({
                "who": display,
                "handle": handle,
                "when": getattr(record, "created_at", None),
                "content": getattr(record, "text", "") or "",
                "url": _post_url_from_uri(uri, handle),
                "uri": uri,
                "source": "bsky",
            })
        cursor = getattr(res, "cursor", None)
        pages += 1
        if not cursor:
            break
        time.sleep(sleep_s)
    return out

# ============================ Public API (easy) ============================

def fetch_bsky_stock_posts(
    symbol: str
) -> List[Dict]:
    """
    ดึงโพสต์ Bluesky ที่พูดถึงหุ้น/สัญลักษณ์:
      - ค้นด้วย 3 คำค้น: <SYM>, $<SYM>, #<SYM> (เช่น NVDA, $NVDA, #NVDA)
      - รวมผล, ลบซ้ำด้วย uri, ใส่ฟิลด์ 'symbol', เรียงเวลาล่าสุดก่อน
      - เซฟเป็น .jsonl อัตโนมัติ (รองรับ placeholder {symbol})

    Credentials:
      - ตั้ง ENV: BSKY_HANDLE, BSKY_APP_PW (แนะนำ) หรือใส่มาทางพารามิเตอร์ก็ได้
    """
    limit_total: int = 180
    handle: Optional[str] = "keingkrai.bsky.social"
    app_password: Optional[str] = "ipki-ujyp-4a7h-ludf"
    service: Optional[str] = None
    save_jsonl_path: Optional[str] = f"data/social/{symbol}/bsky_{symbol}_posts.jsonl"
    # ---- อ่าน credentials จาก env ถ้าไม่ส่งมา ----
    handle = handle or os.getenv("BSKY_HANDLE")
    app_password = app_password or os.getenv("BSKY_APP_PW")
    if not handle or not app_password:
        raise RuntimeError(
            "โปรดตั้งค่า Bluesky credentials: BSKY_HANDLE และ BSKY_APP_PW (App Password) "
            "หรือส่งผ่านอาร์กิวเมนต์ handle=..., app_password=..."
        )

    # ---- login ----
    client = Client()
    if service:
        client.login(handle, app_password, service=service)
    else:
        client.login(handle, app_password)

    q_sym = symbol.upper()
    queries = [q_sym, f"${q_sym}", f"#{q_sym}"]

    # ต่อ query ให้ครบ limit รวม (หารเท่า ๆ กัน)
    per_query = max(1, limit_total // len(queries))
    all_rows: List[Dict] = []
    for q in queries:
        rows = _collect_query(client, q, per_query)
        all_rows.extend(rows)

    # ลบซ้ำด้วย uri
    seen = set()
    uniq: List[Dict] = []
    for r in all_rows:
        u = r.get("uri")
        if not u or u in seen:
            continue
        seen.add(u)
        r["symbol"] = q_sym
        uniq.append(r)

    # เรียงตามเวลา (ISO 8601 string) ใหม่สุดก่อน
    uniq.sort(key=lambda x: x.get("when") or "", reverse=True)

    # บีบให้ไม่เกิน limit_total จริง ๆ
    if len(uniq) > limit_total:
        uniq = uniq[:limit_total]

    # เซฟไฟล์
    if save_jsonl_path:
        try:
            save_path = save_jsonl_path.format(symbol=q_sym)
        except Exception:
            save_path = save_jsonl_path
        save_jsonl(uniq, save_path, append=False)

    return uniq

# ------------------------------ mastodon --------------------------------#
from mastodon import Mastodon
from html import unescape
import re, json, os, time
from datetime import datetime
from urllib.parse import urljoin

def _ensure_dir(path: str):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

def save_jsonl(items: List[Dict], path: str, append: bool = False):
    _ensure_dir(path)
    mode = "a" if append else "w"
    with open(path, mode, encoding="utf-8") as f:
        for obj in items:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def _strip_html(html: str) -> str:
    if not html:
        return ""
    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    text = re.sub(r"<.*?>", "", text, flags=re.DOTALL)
    return unescape(text).strip()

def _to_iso(dt) -> str:
    try:
        return dt.isoformat()
    except Exception:
        return str(dt)

def _mk_client(instance_base_url: str, app_token: Optional[str]) -> Mastodon:
    if app_token:
        return Mastodon(access_token=app_token, api_base_url=instance_base_url)
    return Mastodon(api_base_url=instance_base_url)  # public read

def _timeline_hashtag_all(
    m: Mastodon, tag: str, *, limit_total: int, sleep_s: float = 0.05
) -> List[Dict]:
    """
    ดึง timeline hashtag #<tag> แบบไล่หน้า (max_id) จนครบ limit_total หรือหมด
    """
    out: List[Dict] = []
    max_id = None
    while len(out) < limit_total:
        page = m.timeline_hashtag(tag, limit=min(40, limit_total - len(out)), max_id=max_id)
        if not page:
            break
        for t in page:
            out.append({
                "who": f'{t["account"].get("display_name") or t["account"].get("acct")}',
                "when": _to_iso(t.get("created_at")),
                "content": _strip_html(t.get("content", "")),
                "url": t.get("url") or t.get("uri"),
                "id": str(t.get("id")),
                "source": "mastodon#hashtag",
            })
        max_id = page[-1].get("id")
        time.sleep(sleep_s)
    return out

def _search_statuses(
    m: Mastodon, q: str, *, limit_total: int, sleep_s: float = 0.05
) -> List[Dict]:
    """
    ดึงจาก search results (statuses) — ใช้ search_v2 ได้ก็ใช้, ไม่งั้น fallback เป็น search
    หมายเหตุ: บาง instance จำกัดผลลัพธ์ทีละหน้า ไม่มีคอร์เซอร์ ก็จะดึงได้เท่าที่ API ให้
    """
    try:
        if hasattr(m, "search_v2"):
            res = m.search_v2(q=q, type="statuses", limit=min(40, limit_total), resolve=True)
            statuses = res.get("statuses", []) if isinstance(res, dict) else []
        else:
            res = m.search(q=q, resolve=True, limit=min(40, limit_total))
            statuses = res.get("statuses", []) if isinstance(res, dict) else []
    except Exception:
        statuses = []

    out: List[Dict] = []
    for t in statuses:
        out.append({
            "who": f'{t["account"].get("display_name") or t["account"].get("acct")}',
            "when": _to_iso(t.get("created_at")),
            "content": _strip_html(t.get("content", "")),
            "url": t.get("url") or t.get("uri"),
            "id": str(t.get("id")),
            "source": "mastodon#search",
        })
    time.sleep(sleep_s)
    return out

def fetch_mastodon_stock_posts( symbol: str ) -> List[Dict]:
    """
    ดึงโพสต์ Mastodon ที่เกี่ยวกับหุ้น:
      - Hashtag timeline: #<SYMBOL>
      - Text search: <SYMBOL>, $<SYMBOL>
    รวม, ลบซ้ำ (id), เติม 'symbol', เรียงเวลาใหม่สุดก่อน และบันทึก .jsonl อัตโนมัติ

    ENV ที่รองรับ:
      - MASTODON_BASE_URL (เช่น https://mastodon.social)
      - MASTODON_TOKEN    (app/user token ถ้ามี จะช่วยเพิ่มโควต้า/ข้ามบางข้อจำกัด)
    """
    # ทั้งหมดนี้เป็นค่าเริ่มต้น/อ่านจาก ENV — ผู้ใช้ใส่แค่ symbol ก็พอ
    instance_base_url: Optional[str] = None
    limit_hashtag: int = 120
    limit_search: int = 120
    app_token: Optional[str] = None
    save_jsonl_path: Optional[str] = f"data/social/{symbol}/mastodon_{symbol}_posts.jsonl"
    instance_base_url = instance_base_url or os.getenv("MASTODON_BASE_URL", "https://mastodon.social")
    app_token = app_token or os.getenv("MASTODON_TOKEN")

    m = _mk_client(instance_base_url, app_token)
    tag = symbol.upper()

    # 1) Hashtag timeline
    rows = _timeline_hashtag_all(m, tag, limit_total=limit_hashtag)

    # 2) Search statuses: SYMBOL และ $SYMBOL
    rows += _search_statuses(m, tag,     limit_total=limit_search)
    rows += _search_statuses(m, f"${tag}", limit_total=limit_search)

    # de-dup by id
    seen = set()
    uniq: List[Dict] = []
    for r in rows:
        rid = r.get("id")
        if not rid or rid in seen:
            continue
        seen.add(rid)
        r["symbol"] = tag
        # เติม absolute URL ถ้าจำเป็น (บาง instance ให้เป็น /@user/…)
        if r.get("url") and r["url"].startswith("/"):
            r["url"] = urljoin(instance_base_url, r["url"])
        uniq.append(r)

    # sort latest first
    uniq.sort(key=lambda x: x.get("when") or "", reverse=True)

    # save
    if save_jsonl_path:
        try:
            out_path = save_jsonl_path.format(symbol=tag)
        except Exception:
            out_path = save_jsonl_path
        save_jsonl(uniq, out_path, append=False)

    return uniq

# ------------------------------ Subreddit social ---------------------------------#
import praw

DEFAULT_SUBS = [
    "stocks", "investing", "StockMarket", "wallstreetbets",
    "news", "business", "technology"
]

def _ensure_dir(path: str):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)

def save_jsonl(items: List[Dict], path: str, append: bool = False):
    _ensure_dir(path)
    mode = "a" if append else "w"
    with open(path, mode, encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

def _mk_reddit():
    return praw.Reddit(
        client_id="6ntwQ2TEM4UZNlsjqO9T0A",
        client_secret="GaSCQu0ZMPwLr-zfs9PBFFfVPKrncg",
        user_agent="your-app:v1 (by u/yourname)",
        ratelimit_seconds=5,
    )

def fetch_reddit_symbol_top_praw( symbol: str ) -> List[Dict]:
    """
    ค้นหาโพสต์ที่กล่าวถึง symbol (เช่น NVDA, $NVDA) ในหลาย subreddit
    - เรียงตาม top ภายใน timeframe ที่กำหนด
    - ลบซ้ำด้วย post.id
    - เซฟเป็น JSONL อัตโนมัติ (รองรับ {symbol},{timeframe} ในพาธ)
    """
    timeframe: str = "week"           # "hour","day","week","month","year","all"
    subs: Optional[List[str]] = None  # ถ้า None ใช้ DEFAULT_SUBS
    limit_per_sub: int = 50
    include_selftext: bool = False
    out_path: Optional[str] = f"data/social/{symbol}/reddit_{symbol}_post.jsonl"
    symbol_up = symbol.upper()
    query_variants = [symbol_up, f"${symbol_up}"]

    subs = subs or DEFAULT_SUBS
    reddit = _mk_reddit()
    results: List[Dict] = []
    seen = set()

    for sub in subs:
        sr = reddit.subreddit(sub)
        # รวมผลการค้นหาแต่ละ query variant
        fetched = 0
        for q in query_variants:
            # ใช้ search + sort=top + time_filter
            try:
                for p in sr.search(query=q, sort="top", time_filter=timeframe, limit=limit_per_sub):
                    if getattr(p, "over_18", False):
                        continue
                    if p.id in seen:
                        continue
                    seen.add(p.id)
                    item = {
                        "id": p.id,
                        "subreddit": sub,
                        "title": p.title,
                        "url": p.url,
                        "permalink": f"https://reddit.com{p.permalink}",
                        "created_utc": float(getattr(p, "created_utc", 0.0) or 0.0),
                        "score": getattr(p, "score", None),
                        "num_comments": getattr(p, "num_comments", None),
                        "flair": getattr(p, "link_flair_text", None),
                        "symbol": symbol_up,
                        "query": q,
                    }
                    if include_selftext:
                        item["selftext"] = (getattr(p, "selftext", "") or "").strip()
                    results.append(item)
                    fetched += 1
                    # ระวัง rate-limit นิดนึง
                    time.sleep(0.03)
            except Exception:
                # ถ้าซับปิด/จำกัด ก็ข้าม
                continue

    # sort latest first (ตามเวลาสร้าง)
    results.sort(key=lambda x: x.get("created_utc", 0.0), reverse=True)

    # save
    if out_path:
        try:
            out_path = out_path.format(symbol=symbol_up, timeframe=timeframe)
        except Exception:
            pass
        save_jsonl(results, out_path, append=False)

    return results
# ------------------------------ EDIT FUNDAMENTALS ---------------------------------#

import yfinance as yf
from typing import Dict, List, Optional, Tuple

# =========================
# CONFIG (ตั้งค่าได้ทาง ENV)
# =========================
FINNHUB_API_KEY      = os.getenv("FINNHUB_API_KEY", "d49dhs1r01qshn3lpbn0d49dhs1r01qshn3lpbng")
ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY", "7DJF0DNKIR9T1F9X")
REQUEST_TIMEOUT      = float(os.getenv("REQ_TIMEOUT", "30"))

# เส้นทางบันทึกผล (รองรับ {symbol})
DEFAULT_JSONL_PATH = r"data/fundamental/{symbol}/fundamentals_choice.jsonl"
DEFAULT_JSON_PATH  = r"data/fundamental/{symbol}/fundamentals_choice.json"
DEFAULT_RAW_JSON   = r"data/fundamental/{symbol}/fundamentals_raw.json"
# =========================
# สคีมาฟิลด์ที่ “พยายามเทียบ” ระหว่าง 3 แหล่ง
# =========================
NUM_FIELDS = {
    "overview":        ["marketCap", "sharesOutstanding", "peRatio"],
    "balancesheet":    ["totalAssets", "totalLiabilities", "shareholderEquity"],
    "cashflow":        ["operatingCashFlow", "freeCashFlow", "capitalExpenditures"],
    "incomestatement": ["totalRevenue", "netIncome", "eps"],
}
STR_FIELDS = {
    "overview": ["name", "currency", "exchange", "sector", "industry"],
    "balancesheet": [],
    "cashflow": [],
    "incomestatement": [],
}

PREFERRED_ORDER = ["yfinance", "finnhub", "alphavantage"]   # ใช้เป็นตัวตัดสินสุดท้ายเมื่อคะแนนเสมอ
UNIT_SCALES = [1, 10, 1000, 1_000_000, 1_000_000_000]       # เผื่อค่ามาต่างหน่วย (เช่น billion vs dollar)

# =========================
# IO Helpers
# =========================
def _ensure_dir_for(path: str):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

def _fmt_path(tpl: Optional[str], symbol: str) -> Optional[str]:
    if not tpl:
        return None
    try:
        p = tpl.format(symbol=symbol)
    except Exception:
        p = tpl
    _ensure_dir_for(p)
    return p

def save_json(obj, path: str):
    _ensure_dir_for(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def save_jsonl_line(obj, path: str, append: bool = True):
    _ensure_dir_for(path)
    mode = "a" if append else "w"
    with open(path, mode, encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

# =========================
# Utils
# =========================
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _try_float(x):
    try:
        if x in (None, "", "None", "NaN", "null"):
            return None
        return float(x)
    except Exception:
        return None

def _almost_equal(a: float, b: float, abs_tol=1e-2, rel_tol=1e-3) -> bool:
    diff = abs(a - b)
    return diff <= max(abs_tol, rel_tol * max(abs(a), abs(b), 1e-12))

def _match_units(a: float, b: float) -> bool:
    if a is None or b is None:
        return False
    for sa in UNIT_SCALES:
        for sb in UNIT_SCALES:
            if _almost_equal(a * sa, b * sb):
                return True
    return False

def _str_equal(a: Optional[str], b: Optional[str]) -> bool:
    if not a or not b:
        return False
    return str(a).strip().lower() == str(b).strip().lower()

def _most_recent_col_frame(df) -> Optional[Tuple[str, Dict[str, float]]]:
    try:
        if df is None or getattr(df, "empty", True):
            return None
        col0 = df.columns[0]  # yfinance เรียงคอลัมน์ล่าสุดไว้ซ้าย
        series = df[col0]
        row_dict = {}
        for idx, val in series.items():
            row_dict[str(idx)] = _try_float(val)
        return str(col0), row_dict
    except Exception:
        return None

# =========================
# Fetchers: yfinance
# =========================
def _fetch_yf_overview(symbol: str) -> Dict:
    t = yf.Ticker(symbol)
    out = {}
    try:
        finfo = t.fast_info
        out["marketCap"]         = _try_float(getattr(finfo, "market_cap", None))
        out["sharesOutstanding"] = _try_float(getattr(finfo, "shares_outstanding", None))
        out["peRatio"]           = _try_float(getattr(finfo, "trailing_pe", None))
        out["currency"]          = getattr(finfo, "currency", None)
        out["exchange"]          = getattr(finfo, "exchange", None)
    except Exception:
        pass
    try:
        info = t.get_info()
        out["name"]     = info.get("shortName") or info.get("longName")
        out["sector"]   = info.get("sector")
        out["industry"] = info.get("industry")
        out["exchange"] = out.get("exchange") or info.get("fullExchangeName") or info.get("exchange")
        out["currency"] = out.get("currency") or info.get("currency")
    except Exception:
        pass
    return out

def _fetch_yf_statements(symbol: str) -> Dict[str, Dict]:
    t = yf.Ticker(symbol)

    # Balance Sheet
    bs = {"totalAssets": None, "totalLiabilities": None, "shareholderEquity": None}
    bs_latest = _most_recent_col_frame(getattr(t, "balance_sheet", None))
    if bs_latest:
        _, r = bs_latest
        bs["totalAssets"]       = r.get("Total Assets")
        bs["totalLiabilities"]  = r.get("Total Liab") or r.get("Total Liabilities Net Minority Interest")
        bs["shareholderEquity"] = r.get("Total Stockholder Equity") or r.get("Total Equity Gross Minority Interest")

    # Cash Flow
    cf = {"operatingCashFlow": None, "freeCashFlow": None, "capitalExpenditures": None}
    cf_latest = _most_recent_col_frame(getattr(t, "cashflow", None))
    if cf_latest:
        _, r = cf_latest
        op    = r.get("Total Cash From Operating Activities") or r.get("Operating Cash Flow")
        capex = r.get("Capital Expenditures")
        fcf   = r.get("Free Cash Flow")
        if fcf is None and (op is not None) and (capex is not None):
            fcf = op - capex
        cf["operatingCashFlow"]   = op
        cf["capitalExpenditures"] = capex
        cf["freeCashFlow"]        = fcf

    # Income Statement
    inc = {"totalRevenue": None, "netIncome": None, "eps": None}
    inc_latest = _most_recent_col_frame(getattr(t, "financials", None))
    if inc_latest:
        _, r = inc_latest
        inc["totalRevenue"] = r.get("Total Revenue")
        inc["netIncome"]    = r.get("Net Income")
    try:
        finfo = t.fast_info
        inc["eps"] = _try_float(getattr(finfo, "trailing_eps", None))
    except Exception:
        pass

    return {"balancesheet": bs, "cashflow": cf, "incomestatement": inc}

def fetch_yfinance(symbol: str) -> Dict[str, Dict]:
    return {"overview": _fetch_yf_overview(symbol), **_fetch_yf_statements(symbol)}

# =========================
# Fetchers: Alpha Vantage
# =========================
def _av_get(function: str, symbol: str, apikey: str, params: Optional[Dict]=None) -> Dict:
    if not apikey:
        return {}
    url = "https://www.alphavantage.co/query"
    q = {"function": function, "symbol": symbol, "apikey": apikey}
    if params:
        q.update(params)
    r = requests.get(url, params=q, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    data = r.json()
    if any(k in data for k in ("Note", "Information", "Error Message")):
        return {}
    return data

def fetch_alphavantage(symbol: str) -> Dict[str, Dict]:
    # OVERVIEW
    ov_raw = _av_get("OVERVIEW", symbol, ALPHAVANTAGE_API_KEY)
    overview = {}
    if ov_raw:
        overview = {
            "name": ov_raw.get("Name"),
            "currency": ov_raw.get("Currency"),
            "exchange": ov_raw.get("Exchange"),
            "sector": ov_raw.get("Sector"),
            "industry": ov_raw.get("Industry"),
            "marketCap": _try_float(ov_raw.get("MarketCapitalization")),
            "sharesOutstanding": _try_float(ov_raw.get("SharesOutstanding")),
            "peRatio": _try_float(ov_raw.get("PERatio")),
        }

    # BALANCE_SHEET
    bs = {"totalAssets": None, "totalLiabilities": None, "shareholderEquity": None}
    bs_raw = _av_get("BALANCE_SHEET", symbol, ALPHAVANTAGE_API_KEY)
    rep = (bs_raw.get("annualReports") or [])[:1] if bs_raw else []
    if rep:
        r0 = rep[0]
        bs["totalAssets"]       = _try_float(r0.get("totalAssets"))
        bs["totalLiabilities"]  = _try_float(r0.get("totalLiabilities"))
        bs["shareholderEquity"] = _try_float(r0.get("totalShareholderEquity"))

    # CASH_FLOW
    cf = {"operatingCashFlow": None, "freeCashFlow": None, "capitalExpenditures": None}
    cf_raw = _av_get("CASH_FLOW", symbol, ALPHAVANTAGE_API_KEY)
    rep = (cf_raw.get("annualReports") or [])[:1] if cf_raw else []
    if rep:
        r0 = rep[0]
        op    = _try_float(r0.get("operatingCashflow"))
        capex = _try_float(r0.get("capitalExpenditures"))
        fcf   = _try_float(r0.get("freeCashFlow"))
        if fcf is None and (op is not None) and (capex is not None):
            fcf = op - capex
        cf["operatingCashFlow"]   = op
        cf["capitalExpenditures"] = capex
        cf["freeCashFlow"]        = fcf

    # INCOME_STATEMENT
    inc = {"totalRevenue": None, "netIncome": None, "eps": None}
    inc_raw = _av_get("INCOME_STATEMENT", symbol, ALPHAVANTAGE_API_KEY)
    rep = (inc_raw.get("annualReports") or [])[:1] if inc_raw else []
    if rep:
        r0 = rep[0]
        inc["totalRevenue"] = _try_float(r0.get("totalRevenue"))
        inc["netIncome"]    = _try_float(r0.get("netIncome"))
        inc["eps"]          = _try_float(r0.get("reportedEPS") or r0.get("eps"))

    return {"overview": overview, "balancesheet": bs, "cashflow": cf, "incomestatement": inc}

# =========================
# Fetchers: Finnhub
# =========================
def _fh_get(path: str, params: Optional[Dict]=None) -> Dict:
    if not FINNHUB_API_KEY:
        return {}
    base = "https://finnhub.io/api/v1"
    q = {"token": FINNHUB_API_KEY}
    if params:
        q.update(params)
    r = requests.get(f"{base}/{path}", params=q, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, dict) and data.get("error"):
        return {}
    return data

def fetch_finnhub(symbol: str) -> Dict[str, Dict]:
    # OVERVIEW (profile2)
    prof = _fh_get("stock/profile2", {"symbol": symbol}) or {}
    overview = {
        "name": prof.get("name"),
        "currency": prof.get("currency"),
        "exchange": prof.get("exchange"),
        "sector": prof.get("finnhubIndustry"),
        "industry": prof.get("finnhubIndustry"),
        "marketCap": _try_float(prof.get("marketCapitalization")) * 1_000_000_000 if _try_float(prof.get("marketCapitalization")) is not None else None,
        "sharesOutstanding": _try_float(prof.get("shareOutstanding")),
        "peRatio": None,
    }
    try:
        met = _fh_get("stock/metric", {"symbol": symbol, "metric": "all"})
        overview["peRatio"] = _try_float((met.get("metric") or {}).get("peTTM"))
    except Exception:
        pass

    # FINANCIALS-REPORTED → ล่าสุด
    rep = _fh_get("stock/financials-reported", {"symbol": symbol}) or {}
    data = rep.get("data") or []
    bs = {"totalAssets": None, "totalLiabilities": None, "shareholderEquity": None}
    cf = {"operatingCashFlow": None, "freeCashFlow": None, "capitalExpenditures": None}
    inc = {"totalRevenue": None, "netIncome": None, "eps": None}
    if data:
        latest = data[0]
        report = latest.get("report") or {}
        bs_list = report.get("bs") or []
        cf_list = report.get("cf") or []
        ic_list = report.get("ic") or []

        def _pick(items: List[Dict], keys: List[str]) -> Optional[float]:
            for k in keys:
                for it in items:
                    c = str(it.get("concept") or it.get("label") or "").lower()
                    if c == k.lower():
                        return _try_float(it.get("value"))
            return None

        # balance
        bs["totalAssets"]       = _pick(bs_list, ["TotalAssets"])
        bs["totalLiabilities"]  = _pick(bs_list, ["Liabilities"]) or _pick(bs_list, ["LiabilitiesCurrent"]) or _pick(bs_list, ["LiabilitiesNoncurrent"])
        bs["shareholderEquity"] = _pick(bs_list, ["StockholdersEquity"]) or _pick(bs_list, ["Equity"]) or _pick(bs_list, ["EquityAttributableToParent"])

        # cashflow
        op  = _pick(cf_list, ["NetCashProvidedByUsedInOperatingActivities", "NetCashProvidedByOperatingActivities"])
        cap = _pick(cf_list, ["PaymentsToAcquirePropertyPlantAndEquipment", "CapitalExpenditures"])
        fcf = None
        if (op is not None) and (cap is not None):
            fcf = op - cap
        cf["operatingCashFlow"]   = op
        cf["capitalExpenditures"] = cap
        cf["freeCashFlow"]        = fcf

        # income
        inc["totalRevenue"] = _pick(ic_list, ["Revenues", "SalesRevenueNet"])
        inc["netIncome"]    = _pick(ic_list, ["NetIncomeLoss", "ProfitLoss"])
        inc["eps"]          = _pick(ic_list, ["EarningsPerShareBasic", "EarningsPerShareDiluted"])

    return {"overview": overview, "balancesheet": bs, "cashflow": cf, "incomestatement": inc}

# =========================
# Scoring & Picking
# =========================
def _score_section(section: str, by_src: Dict[str, Dict]) -> Dict[str, int]:
    srcs = ["yfinance", "finnhub", "alphavantage"]
    score = {s: 0 for s in srcs}
    nums = NUM_FIELDS.get(section, [])
    strs = STR_FIELDS.get(section, [])

    for f in nums:
        vals = {s: _try_float((by_src.get(s) or {}).get(f)) for s in srcs}
        for a, b in [("yfinance","finnhub"), ("yfinance","alphavantage"), ("finnhub","alphavantage")]:
            va, vb = vals.get(a), vals.get(b)
            if isinstance(va, (int, float)) and isinstance(vb, (int, float)) and _match_units(va, vb):
                score[a] += 1; score[b] += 1

    for f in strs:
        vals = {s: (by_src.get(s) or {}).get(f) for s in srcs}
        for a, b in [("yfinance","finnhub"), ("yfinance","alphavantage"), ("finnhub","alphavantage")]:
            if _str_equal(vals.get(a), vals.get(b)):
                score[a] += 1; score[b] += 1
    return score


# ===== แทนที่/เพิ่มฟังก์ชัน completeness ให้เป็น dict ต่อแหล่ง =====
def _completeness_section(section: str, by_src: Dict[str, Dict]) -> Dict[str, int]:
    """
    นับ 'ฟิลด์ที่มีข้อมูล' ต่อแหล่ง (ยึดตาม NUM_FIELDS + STR_FIELDS ของ section นั้น)
    คืนค่า: {"yfinance": <int>, "finnhub": <int>, "alphavantage": <int>}
    """
    fields = (NUM_FIELDS.get(section, []) or []) + (STR_FIELDS.get(section, []) or [])
    srcs = ["yfinance", "finnhub", "alphavantage"]
    comp = {s: 0 for s in srcs}

    for s in srcs:
        d = by_src.get(s) or {}
        cnt = 0
        for f in fields:
            v = d.get(f)
            # มีตัวเลขที่เป็น finite
            if isinstance(v, (int, float)) and not (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
                cnt += 1
            # มี string ที่ไม่ว่าง
            elif isinstance(v, str) and v.strip():
                cnt += 1
        comp[s] = cnt
    return comp


def _winner(total_score: Dict[str,int], total_comp: Dict[str,int]) -> str:
    top = max(total_score.values())
    cands = [s for s, sc in total_score.items() if sc == top]
    if len(cands) == 1:
        return cands[0]
    best_comp = max(total_comp[s] for s in cands)
    cands2 = [s for s in cands if total_comp[s] == best_comp]
    if len(cands2) == 1:
        return cands2[0]
    for s in PREFERRED_ORDER:
        if s in cands2:
            return s
    return cands2[0]

# =========================
# Orchestrator (ดึง→เทียบ→เลือก)
# =========================
def fetch_all_fundamentals(symbol: str) -> Dict:
    y = fetch_yfinance(symbol)
    time.sleep(0.4)
    f = fetch_finnhub(symbol) if FINNHUB_API_KEY else {"overview":{}, "balancesheet":{}, "cashflow":{}, "incomestatement":{}}
    time.sleep(0.4)
    a = fetch_alphavantage(symbol) if ALPHAVANTAGE_API_KEY else {"overview":{}, "balancesheet":{}, "cashflow":{}, "incomestatement":{}}

    # write text file
    report_message = f"\nFetched fundamentals for {symbol}:\n"
    # count each source
    report_message += f"- YFinance: {sum(1 for sec in y.values() if any(v is not None for v in sec.values()))} fields fetched\n"
    report_message += f"- Finnhub: {sum(1 for sec in f.values() if any(v is not None for v in sec.values()))} fields fetched\n"
    report_message += f"- AlphaVantage: {sum(1 for sec in a.values() if any(v is not None for v in sec.values()))} fields fetched"

    with open("all_report_message.txt", "a") as file:
        file.write(report_message + "\n")

    return {"symbol": symbol, "raw": {"yfinance": y, "finnhub": f, "alphavantage": a}}

def decide_single_source(fetched: Dict) -> Dict:
    symbol = fetched.get("symbol")
    raw = fetched.get("raw") or {}
    y, f, a = raw.get("yfinance", {}), raw.get("finnhub", {}), raw.get("alphavantage", {})

    sections = ["overview", "balancesheet", "cashflow", "incomestatement"]
    total_score = {"yfinance":0, "finnhub":0, "alphavantage":0}
    total_comp  = {"yfinance":0, "finnhub":0, "alphavantage":0}
    detail = {}

    for sec in sections:
        by_src = {"yfinance": y.get(sec, {}), "finnhub": f.get(sec, {}), "alphavantage": a.get(sec, {})}
        sscore = _score_section(sec, by_src)
        scomp  = _completeness_section(sec, by_src)
        for k in total_score: total_score[k] += sscore[k]
        for k in total_comp:  total_comp[k]  += scomp[k]
        detail[sec] = {"scores": sscore, "completeness": scomp}

    winner = _winner(total_score, total_comp)
    final_payload = {
        "overview":        (raw.get(winner, {}) or {}).get("overview", {}),
        "balancesheet":    (raw.get(winner, {}) or {}).get("balancesheet", {}),
        "cashflow":        (raw.get(winner, {}) or {}).get("cashflow", {}),
        "incomestatement": (raw.get(winner, {}) or {}).get("incomestatement", {}),
    }
    return {
        "symbol": symbol,
        "chosen_source": winner,
        "scores": total_score,
        "completeness": total_comp,
        "sections": detail,
        "final_payload": final_payload,
        "raw": raw,
        "timestamp": _now_iso(),
    }
    
def sent_fundamental_to_telegram(report_message, score: dict, chosen_source: str):
    """Send comparison result to Telegram bot."""
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    MESSAGE = f"Fundamental Data Source Comparison Result:\n\n" \
                f"{report_message}\n" \
              f"\n===== SIMILARITY SCORE =====\n"\
              f"YFinance Score: {score['yfinance']}\n" \
              f"AlphaVantage Score: {score['alphavantage']}\n" \
              f"Finnhub Score: {score['finnhub']}\n\n" \
              f"Best Source: {chosen_source.upper()}"
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": MESSAGE
    }
    
    # resp = requests.post(url, data=data)
    # print(resp.json())

def pick_fundamental_source(symbol: str) -> Dict:
    """จ่ายแค่ symbol → ได้ผลลัพธ์ (แหล่งเดียวที่เลือก) และบันทึก JSONL/JSON ตาม path ที่กำหนดไว้แล้ว"""
    save_jsonl_path: Optional[str] = DEFAULT_JSONL_PATH
    save_json_path:  Optional[str] = DEFAULT_JSON_PATH
    save_raw_json_path: Optional[str] = DEFAULT_RAW_JSON
    fetched = fetch_all_fundamentals(symbol)
    result  = decide_single_source(fetched)

    # บันทึก raw (ออปชัน)
    raw_path = _fmt_path(save_raw_json_path, symbol)
    if raw_path:
        save_json({"symbol": symbol, "timestamp": result["timestamp"], "raw": result["raw"]}, raw_path)

    # บันทึกผลสรุปเป็น JSON ปกติ (ออปชัน)
    json_path = _fmt_path(save_json_path, symbol)
    if json_path:
        # ตัด raw ออกจากไฟล์สรุปเพื่อให้เบา
        to_save = {k: v for k, v in result.items() if k != "raw"}
        save_json(to_save, json_path)

    # บันทึกผลสรุปเป็น JSONL (มี 1 บรรทัดต่อการรัน)
    jsonl_path = _fmt_path(save_jsonl_path, symbol)
    if jsonl_path:
        to_line = {
            "timestamp": result["timestamp"],
            "symbol": result["symbol"],
            "chosen_source": result["chosen_source"],
            "scores": result["scores"],
            "completeness": result["completeness"],
            "final_payload": result["final_payload"],
        }
        save_jsonl_line(to_line, jsonl_path, append=True)
    
    # ส่งผลการเปรียบเทียบไปยัง Telegram (ถ้ามีการตั้งค่า)
    # if os.getenv("TELEGRAM_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"):
    #     sent_fundamental_to_telegram(
    #         report_message=f"Fundamental data for {symbol} has been processed.",
    #         score=result["scores"],
    #         chosen_source=result["chosen_source"]
    #     )
        
    print(f"\n\n\n📜 Fundamental data for {symbol}. Chosen source: {result['chosen_source']}\n\n\n")

    report_message = f"📜 Fundamental data for {symbol}. Chosen source: {result['chosen_source']}"

    # write text file
    with open("all_report_message.txt", "a", encoding='utf-8') as file:
        file.write(report_message + "\n")

    return result
