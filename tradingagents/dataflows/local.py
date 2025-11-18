from __future__ import annotations

from tkinter import END
from typing import Annotated
import pandas as pd
import os
from .config import DATA_DIR
from datetime import datetime
from dateutil.relativedelta import relativedelta
import json
from .reddit_utils import fetch_top_from_category
from tqdm import tqdm
from tradingview_ta import TA_Handler, Interval
import json

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

def get_reddit_company_news(
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
from datetime import datetime, timezone
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
# pip install requests pandas
import os, requests

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
    "rsi",            # rsi
    "boll_ub",        # Bollinger upper band
    "boll_lb",        # Bollinger lower band
]

# tolerance ต่ออินดิเคเตอร์ (จูนได้)
INDICATOR_TOL = {
    "rsi":            {"abs": 0.25, "rel": 0.0},
    "macd":           {"abs": 0.005, "rel": 0.0},
    "close_10_ema":   {"abs": 0.03,  "rel": 6e-4},
    "close_50_sma":   {"abs": 0.04,  "rel": 6e-4},
    "close_200_sma":  {"abs": 0.06,  "rel": 6e-4},
    "boll_ub":        {"abs": 0.06,  "rel": 7e-4},
    "boll_lb":        {"abs": 0.06,  "rel": 7e-4},
}

# ===========================
# Pick ONE source per indicator (prefer TV > YF > TD)
# ===========================

from typing import Optional

SOURCE_PRIORITY_DEFAULT = ("tradingview", "yfinance", "twelvedata")

def _first_numeric(d: dict, keys_in_priority: tuple[str, ...]) -> tuple[Optional[str], Optional[float]]:
    """
    คืน (source, value) แหล่งแรกที่มีค่าตัวเลข ตามลำดับความสำคัญใน keys_in_priority
    ถ้าไม่เจอคืน (None, None)
    """
    for src in keys_in_priority:
        v = d.get(src)
        if isinstance(v, (int, float)):
            return src, float(v)
    return None, None

def choose_single_source_fixed6(
    *,
    tv: Optional[dict] = None,
    yf: Optional[dict] = None,
    td: Optional[dict] = None,
    priority: tuple[str, ...] = SOURCE_PRIORITY_DEFAULT,
    decimals: int = 6,
) -> dict:
    """
    เลือกผลลัพธ์ 'แหล่งเดียวต่อหัวข้อ' ตามลำดับความสำคัญ:
      tradingview → yfinance → twelvedata
    คืน dict รูปแบบ:
      {
        "<key>": {"source": "tradingview" | "yfinance" | "twelvedata" | None,
                  "value": <float|None>}
      }
    """
    tv = tv or {}
    yf = yf or {}
    td = td or {}

    # รวมเป็นโครงสร้างต่อหัวข้อ
    # { key: { 'tradingview': val, 'yfinance': val, 'twelvedata': val } }
    combined = {}
    for k in COMPARE_KEYS:
        combined[k] = {
            "tradingview": tv.get(k, None),
            "yfinance":    yf.get(k, None),
            "twelvedata":  td.get(k, None),
        }

    out = {}
    for k, d in combined.items():
        src, val = _first_numeric(d, priority)
        if src is None:
            out[k] = {"source": None, "value": None}
        else:
            out[k] = {"source": src, "value": round(val, decimals)}
    return out

def format_choices_markdown(choices: dict) -> str:
    """
    สรุปผลที่เลือกเป็นตาราง Markdown (อ่านง่าย)
    """
    title_map = {
        "close_50_sma":  "50 SMA",
        "close_200_sma": "200 SMA",
        "close_10_ema":  "10 EMA",
        "macd":          "MACD",
        "rsi":           "RSI",
        "boll_ub":       "Bollinger Upper Band",
        "boll_lb":       "Bollinger Lower Band",
    }
    lines = []
    lines.append("## indicators")
    lines.append("| Indicator | Source | Value |")
    lines.append("|---|---|---|")
    for k in COMPARE_KEYS:
        entry = choices.get(k, {"source": None, "value": None})
        src = entry.get("source", None) or "–"
        val = entry.get("value", None)
        val_str = "–" if val is None else f"{val}"
        lines.append(f"| {title_map.get(k,k)} | {src} | {val_str} |")
    lines.append("")
    return "\n".join(lines)

# ------------------------------
# Orchestrator: fetch → choose (auto-skip rate limits)
# ------------------------------
def fetch_and_choose(
    symbol: str,
    *,
    tv_exchange: str = "NASDAQ",
    tv_screener: str = "america",
    tv_interval: str = "1d",
    yf_period: str = "2y",
    yf_interval: str = "1d",
    td_interval: str = "1day",
    decimals: int = 6,
    priority: tuple[str, ...] = SOURCE_PRIORITY_DEFAULT,
    as_markdown: bool = False,
):
    """
    ดึงค่าอินดิเคเตอร์จากแต่ละแหล่ง (ข้ามแหล่งที่เออเรอร์/ลิมิต)
    แล้วเลือกผล 'แหล่งเดียวต่อหัวข้อ' ตามลำดับความสำคัญ:
      tradingview → yfinance → twelvedata
    - as_markdown=True จะคืนเป็นข้อความตาราง Markdown
    """
    sources = {}

    try:
        tv = get_tradingview_indicators_dict(
            symbol, exchange=tv_exchange, screener=tv_screener, interval=tv_interval
        )
        if tv:
            sources["tv"] = tv
    except Exception:
        pass

    try:
        yf = get_yfin_indicators_online_dict(
            symbol, period=yf_period, interval=yf_interval
        )
        if yf:
            sources["yf"] = yf
    except Exception:
        pass

    try:
        td = get_twelve_data_indicator(symbol, interval=td_interval)
        if td:
            sources["td"] = td
    except Exception:
        pass

    if not sources:
        return {
            "error": "no_sources_available",
            "note": "ไม่สามารถดึงค่าจากทุกแหล่งได้ในตอนนี้",
        }

    choices = choose_single_source_fixed6(
        tv=sources.get("tv"),
        yf=sources.get("yf"),
        td=sources.get("td"),
        priority=priority,
        decimals=decimals,
    )

    if as_markdown:
        return format_choices_markdown(choices)
    return choices

# ------------------------------ EDIT NEWS(GLOBAL) -----------------------------------------#

import os, time, json
from typing import Iterable, List, Dict, Optional, Literal, Tuple
from datetime import datetime, timezone
from dateutil import parser as dtparser

import pandas as pd
import finnhub

# -----------------------
# Utilities (I/O + time)
# -----------------------

def save_json(data, path: str):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_jsonl(items: Iterable[dict], path: str, append: bool = False):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    mode = "a" if append else "w"
    with open(path, mode, encoding="utf-8") as f:
        for obj in items:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def _to_iso_utc(ts) -> str:
    """รับ epoch seconds / ISO string → คืน ISO (UTC)"""
    if ts is None:
        return ""
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat().replace("+00:00","Z")
    dt = dtparser.parse(str(ts))
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.isoformat().replace("+00:00","Z")

def _within(dt_iso: str, start: Optional[str], end: Optional[str]) -> bool:
    if not dt_iso:
        return False
    t = dtparser.parse(dt_iso)
    if start and t < dtparser.parse(start): return False
    if end   and t > dtparser.parse(end):   return False
    return True

# -----------------------
# Core fetch functions
# -----------------------

def make_finnhub_client(api_key: Optional[str] = None) -> finnhub.Client:
    """สร้าง finnhub.Client จากพารามิเตอร์หรือ ENV FINNHUB_API_KEY"""
    key = api_key or os.getenv("FINNHUB_API_KEY")
    if not key:
        raise RuntimeError("Missing FINNHUB_API_KEY (pass api_key=... หรือ set ใน environment)")
    return finnhub.Client(api_key=key)

def fetch_general_news_paged(
    client: finnhub.Client,
    category: str = "general",
    *,
    max_pages: int = 3,
    sleep_s: float = 0.6,
    start_min_id: int = 0,
    retries: int = 2,
) -> List[dict]:
    """
    ดึงข่าวทั่วไปแบบแบ่งหน้าโดยใช้ min_id ต่อเนื่อง
    คืนค่าเป็น raw list (จาก API) ต่อกันทุกหน้า
    """
    all_items: List[dict] = []
    min_id = start_min_id
    for _ in range(max_pages):
        last_err = None
        for attempt in range(retries + 1):
            try:
                batch = client.general_news(category, min_id=min_id) or []
                break
            except Exception as e:
                last_err = e
                if attempt < retries:
                    time.sleep(0.8 + attempt * 0.5)
                else:
                    raise
        if not batch:
            break
        all_items.extend(batch)
        min_id = batch[-1].get("id", min_id)
        if sleep_s > 0:
            time.sleep(sleep_s)
    return all_items

# -----------------------
# Projection / Canonical
# -----------------------

WANTED_KEYS = {"datetime", "headline", "id", "source", "summary", "url"}

def project_fields(items: List[dict]) -> List[dict]:
    """
    เลือกเฉพาะฟิลด์ที่ต้องการ + แปลง datetime → ISO UTC
    """
    out: List[dict] = []
    for it in items:
        obj = {k: it.get(k) for k in WANTED_KEYS}
        obj["datetime"] = _to_iso_utc(obj.get("datetime"))
        out.append(obj)
    return out

def filter_by_date(items: List[dict], start_date: Optional[str], end_date: Optional[str]) -> List[dict]:
    """กรองรายการตามช่วงเวลา (YYYY-MM-DD หรือ ISO ก็ได้)"""
    if not (start_date or end_date):
        return items
    out: List[dict] = []
    for it in items:
        if _within(it.get("datetime",""), start_date, end_date):
            out.append(it)
    return out

# -----------------------
# Public high-level API
# -----------------------

def get_finnhub_general_news(
    category: Literal["general","forex","crypto","merger"] = "general",
    *,
    start_date: Optional[str] = None,  # "YYYY-MM-DD" หรือ ISO string
    end_date: Optional[str] = None,    # "
    max_pages: int = 3,
    sleep_s: float = 0.6,
    api_key: Optional[str] = None,
    output: Literal["list","df","markdown"] = "list",
    save_to: Optional[str] = None,     # .json หรือ .jsonl (อัตโนมัติ)
) -> Tuple[object, List[dict]]:
    """
    ดึงข่าวทั่วไปจาก Finnhub → project fields → กรองช่วงเวลา (ถ้ามี)
    Args:
        category: หมวดข่าวของ Finnhub (ค่าเริ่มต้น "general")
        start_date/end_date: กรองช่วงเวลา
        max_pages/sleep_s: ควบคุมการแบ่งหน้า/พักระหว่างเรียก
        api_key: ถ้าไม่ส่งจะอ่านจาก ENV FINNHUB_API_KEY
        output: "list" | "df" | "markdown"
        save_to: ถ้าระบุไฟล์ .json หรือ .jsonl จะเซฟผลลัพธ์ให้ (เฉพาะ projected&filtered)
    Returns:
        (result, items)  โดย result = ตาม output, items = list[dict] (projected & filtered)
    """
    client = make_finnhub_client(api_key="d49dhs1r01qshn3lpbn0d49dhs1r01qshn3lpbng")

    raw = fetch_general_news_paged(
        client,
        category=category,
        max_pages=max_pages,
        sleep_s=sleep_s,
    )
    items = project_fields(raw)
    items = filter_by_date(items, start_date, end_date)

    # save ถ้ากำหนด
    if save_to:
        ext = os.path.splitext(save_to)[-1].lower()
        if ext == ".json":
            save_json(items, save_to)
        elif ext == ".jsonl":
            save_jsonl(items, save_to, append=False)
        else:
            raise ValueError("save_to ต้องลงท้ายด้วย .json หรือ .jsonl")

    # รูปแบบผลลัพธ์
    if output == "list":
        return items, items
    elif output == "df":
        df = pd.DataFrame(items)
        return df, items
    elif output == "markdown":
        md_lines = []
        for i, n in enumerate(items, 1):
            ts = (n.get("datetime") or "").replace("T"," ").replace("Z"," UTC")
            headline = n.get("headline") or ""
            src = n.get("source") or ""
            url = n.get("url") or ""
            md_lines.append(f"{i}. [{ts}] {headline} ({src})" + (f" — {url}" if url else ""))
            if n.get("summary"):
                md_lines.append(f"   \n   {n['summary']}")
        md = "\n".join(md_lines) if md_lines else "(no news)"
        return md, items
    else:
        raise ValueError("output must be one of: 'list','df','markdown'")
    
# ------------------------------ EDIT NEWS GLOBAL(REDDIT) -----------------------------------------#
    
import os, time, json
from typing import Iterable, List, Dict, Optional
from datetime import datetime, timezone
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


# ---------------------------
# Fetchers
# ---------------------------

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


# ---------------------------
# Orchestrators
# ---------------------------

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


def fetch_reddit_world_news(
    out_path: str = "C:\\TradingAgents_fail\\data\\global_news\\reddit_world_news.jsonl",
    subs: Iterable[str] = DEFAULT_SUBS,
    *,
    per_sub_limit: int = 20,
        time_filter: str = "day",
        jsonl: bool = True,
) -> str:
    """
    ดึง → รวม → เซฟเป็นไฟล์ (JSONL เป็นค่าเริ่มต้น)
    คืน path ของไฟล์ที่บันทึก
    """
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

import os, json
from typing import List, Dict, Optional, Iterable, Tuple
from datetime import datetime, timedelta, timezone
from yfinance import Search


# ---------------------------
# Time & IO helpers
# ---------------------------

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


# ---------------------------
# Normalization
# ---------------------------

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

def get_world_news_yf(
    curr_date: str = datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    look_back_days: int = 7,
    limit: int = 50,
    *,
    keywords: Optional[Iterable[str]] = None,
    per_keyword: Optional[int] = None,
    save_jsonl_path: Optional[str] = "C:\\TradingAgents_fail\\data\\global_news\\yfinance_world_news.jsonl",
) -> List[Dict]:
    """
    ดึง 'ข่าวโลก' ด้วย yfinance (ค้นหลายคีย์เวิร์ดทั่วไป):
      1) นิยามหน้าต่างเวลา [curr_date - look_back_days, curr_date]
      2) ดึงข่าวจากหลายคีย์เวิร์ด
      3) รวม/ลบซ้ำ/กรองวัน/เรียง → ตัดตาม limit
      4) (ออปชัน) เซฟ JSON/JSONL

    return: list[dict] ที่ normalize แล้ว
    """
    start_epoch, end_epoch = _window_epochs(curr_date, look_back_days)
    kw = list(keywords) if keywords else DEFAULT_WORLD_KEYWORDS

    # เผื่อดึงเกินมาบ้างเพื่อดีดซ้ำออก (ประมาณการแบบง่าย)
    if per_keyword is None:
        per_keyword = max(10, min(100, (limit // max(1, len(kw))) * 2 or 20))

    items = fetch_yf_news_by_keywords(
        kw,
        start_epoch=start_epoch,
        end_epoch=end_epoch,
        per_keyword=per_keyword,
        limit_total=limit,
    )

    if save_jsonl_path:
        _save_jsonl(items, save_jsonl_path, append=False)

    return items

# ------------------------------ EDIT NEWS(PER_STOCK) -----------------------------------------#
# --------------------------- finnhub ------------------------#
import os, json
from typing import List, Dict, Optional, Iterable, Tuple
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

# ---------------------------
# Time helpers
# ---------------------------

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

def finnhub_get_company_news(
    symbol: str,
    *,
    # Finnhub window
    start_date: Optional[str] = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d"),
    end_date: Optional[str] = datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    # runtime
    limit: int = 100,
    save_jsonl_path: Optional[str] = "C:\\TradingAgents_fail\\data\\stock\\{symbol}\\finnhub_company_news.jsonl",
) -> List[Dict]:
    """
    Orchestrator: ดึงข่าวบริษัทจาก Finnhub + yfinance → รวม/ลบซ้ำ/เรียง/ตัด
    - อย่างน้อยควรส่งช่วงวันสำหรับ Finnhub (start_date/end_date)
    - ถ้าอยากกรอง yfinance ด้วย ก็ส่ง curr_date + look_back_days เพิ่ม
    """
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
import os, time, json, requests, re
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
def reddit_get_company_news(
    sub: str = "news",
    start_dt: datetime = datetime.now(tz=timezone.utc) - timedelta(days=30),
    end_dt: datetime   = datetime.now(tz=timezone.utc),
    query: str = None,
    limit: int = 50,
    save_path: str | None = None,   # << ใหม่: ส่ง path เองได้ ถ้าไม่ส่งจะ generate ให้
):
    """
    ค้นใน subreddit เดียวด้วย restrict_sr + sort=top (เวอร์ชันเรียบง่าย)
    - ถ้าไม่ส่ง save_path → จะสร้าง path อัตโนมัติ: C:\TradingAgents_fail\data\stock\<query>\reddit_search_<sub>_<YYYYMMDD>_<YYYYMMDD>.jsonl
    - สร้างโฟลเดอร์ปลายทางให้เสมอ
    """
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
        save_path = rf"C:\TradingAgents_fail\data\stock\{qslug}\reddit_get_company_news_{end_str}.jsonl"

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
    return out

# ------------------------------ news stock yfinance -----------------------------------------#
import os, json
from typing import List, Dict
import yfinance as yf
from datetime import datetime, timezone

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
    - ใส่แค่ symbol อย่างเดียว
    - เซฟไฟล์อัตโนมัติไว้ที่ ./data/stock/<symbol>/:
        - yfinance_company_news_<YYYY-MM-DD>.json
        - yfinance_company_news_<YYYY-MM-DD>.jsonl
    - คืนค่าลิสต์ข่าวแบบ raw ตาม yfinance
    """
    t = yf.Ticker(symbol)
    try:
        news = t.get_news()            # บางเวอร์ชันของ yfinance
    except Exception:
        news = getattr(t, "news", []) or []

    # เซฟแบบ raw ทั้งหมด
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    base = os.path.join(".", "data", "stock", symbol.lower())
    jsonl_path = os.path.join(base, f"yfinance_company_news_{today}.jsonl")
    _save_jsonl(news, jsonl_path, append=False)

    return news
# ------------------------------ EDIT SOCIAL MEDIA ---------------------------------#
# ------------------------------  BlueSky  ---------------------------------#
import os, json, time
from typing import List, Dict, Optional
from datetime import datetime, timezone
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
    symbol: str,
    *,
    # ให้ใส่แค่ symbol ก็พอ: ที่เหลือมีค่า default ทั้งหมด
    limit_total: int = 180,
    handle: Optional[str] = "keingkrai.bsky.social",
    app_password: Optional[str] = "ipki-ujyp-4a7h-ludf",
    service: Optional[str] = None,
    save_jsonl_path: Optional[str] = r"C:\TradingAgents_fail\data\\social\\{symbol}\\bsky_{symbol}_posts.jsonl",
) -> List[Dict]:
    """
    ดึงโพสต์ Bluesky ที่พูดถึงหุ้น/สัญลักษณ์:
      - ค้นด้วย 3 คำค้น: <SYM>, $<SYM>, #<SYM> (เช่น NVDA, $NVDA, #NVDA)
      - รวมผล, ลบซ้ำด้วย uri, ใส่ฟิลด์ 'symbol', เรียงเวลาล่าสุดก่อน
      - เซฟเป็น .jsonl อัตโนมัติ (รองรับ placeholder {symbol})

    Credentials:
      - ตั้ง ENV: BSKY_HANDLE, BSKY_APP_PW (แนะนำ) หรือใส่มาทางพารามิเตอร์ก็ได้
    """
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
# ------------------------------ EDIT FUNDAMENTALS ---------------------------------#