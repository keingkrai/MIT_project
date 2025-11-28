import os
import sys
import pandas as pd
import io
import re
import requests
from langchain_core.tools import tool
from typing import Annotated

# --- Import Provider Functions ---
# ตรวจสอบ Path ให้ตรงกับโปรเจกต์ของคุณ
from tradingagents.dataflows.y_finance import get_YFin_data_online
from tradingagents.dataflows.alpha_vantage_stock import get_alpha_vantage_stock
from tradingagents.dataflows.trading_view import get_TV_data_online
from tradingagents.dataflows.twelve_data import get_twelvedata_stock

# ==========================================
# Helper Functions
# ==========================================

def to_df(csv_string: str) -> pd.DataFrame:
    """Convert CSV string to pandas DataFrame."""
    if not csv_string or csv_string.strip() == "":
        return pd.DataFrame()
    try:
        return pd.read_csv(io.StringIO(csv_string))
    except Exception:
        return pd.DataFrame()

def extract_record_count(header: str) -> int:
    """Extract 'Total records: XXX' from header."""
    if not header:
        return 0
    match = re.search(r"Total records:\s*(\d+)", header)
    if match:
        return int(match.group(1))
    return 0

def sent_to_telegram(report_message, score: dict, best_source: str):
    """Send comparison result to Telegram bot."""
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    
    if not TOKEN or not CHAT_ID:
        return

    MESSAGE = (f"🏷️ Stock Data Source Comparison Result:\n\n"
               f"{report_message}\n"
               f"===== SIMILARITY SCORE =====\n"
               f"YFinance Score: {score.get('yf', 0)}\n"
               f"TwelveData Score: {score.get('tw', 0)}\n"
               f"TradingView Score: {score.get('tv', 0)}\n\n"
               f"🏆 Best Source: {best_source.upper()}")
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": MESSAGE
    }

    # write text file
    with open("all_report_message.txt", "w", encoding='utf-8') as file:
        file.write(MESSAGE + "\n\n")

    # try:
    #     requests.post(url, data=data, timeout=5)
    # except Exception as e:
    #     print(f"Telegram Error: {e}")

# ==========================================
# Core Logic: Compare Providers
# ==========================================

def compare_stock_providers(symbol, start_date, end_date):
    print(f"\n🚀 Fetching & Comparing Data for {symbol} ({start_date} to {end_date})...")

    # Dictionary เก็บข้อมูลดิบของแต่ละเจ้า
    raw_data = {
        "yfinance": {"header": "", "csv": "", "count": 0},
        "twelvedata": {"header": "", "csv": "", "count": 0},
        "tradingview": {"header": "", "csv": "", "count": 0},
    }

    # --- 1. Call Each Provider (Safely) ---
    # YFinance
    try:
        h, c = get_YFin_data_online(symbol, start_date, end_date)
        raw_data["yfinance"] = {"header": h, "csv": c, "count": extract_record_count(h)}
    except Exception as e:
        print(f"⚠️ YFinance Failed: {e}")

    # TwelveData
    try:
        h, c = get_twelvedata_stock(symbol, start_date, end_date)
        raw_data["twelvedata"] = {"header": h, "csv": c, "count": extract_record_count(h)}
    except Exception as e:
        print(f"⚠️ TwelveData Failed: {e}")

    # TradingView
    try:
        h, c = get_TV_data_online(symbol, start_date, end_date)
        raw_data["tradingview"] = {"header": h, "csv": c, "count": extract_record_count(h)}
    except Exception as e:
        print(f"⚠️ TradingView Failed: {e}")

    # --- 2. Convert to DataFrames & Pre-process ---
    df_yf = to_df(raw_data["yfinance"]["csv"])
    df_tw = to_df(raw_data["twelvedata"]["csv"])
    df_tv = to_df(raw_data["tradingview"]["csv"])

    # Standardize Date column for merging
    if not df_yf.empty: df_yf["Date"] = pd.to_datetime(df_yf["Date"])
    if not df_tw.empty: df_tw["Date"] = pd.to_datetime(df_tw["Date"])
    if not df_tv.empty: df_tv["Date"] = pd.to_datetime(df_tv["Date"])

    # --- 3. Report Message & Initial Check ---
    report_message = "===== TOTAL RECORDS CHECK =====\n"
    report_message += f"YFinance:      {raw_data['yfinance']['count']}\n"
    report_message += f"TwelveData:    {raw_data['twelvedata']['count']}\n"
    report_message += f"TradingView:   {raw_data['tradingview']['count']}\n\n"

    print(report_message)

    # ถ้าไม่มีข้อมูลเลยสักเจ้า ให้ Return Error
    if df_yf.empty and df_tw.empty and df_tv.empty:
        return f"# Error: No data found for {symbol} from any source.\n", ""

    # --- 4. Scoring for Similarity ---
    score = {"yfinance": 0, "twelvedata": 0, "tradingview": 0}
    compare_cols = ["Open", "Close"] # เปรียบเทียบแค่ Open/Close เพื่อความเร็ว

    # Helper function to compare two dataframes
    def calculate_match(df1, df2, suffix1, suffix2):
        if df1.empty or df2.empty: return 0
        try:
            merged = df1.merge(df2, on="Date", suffixes=(suffix1, suffix2), how="inner")
            if merged.empty: return 0
            
            total_matches = 0
            for col in compare_cols:
                # ใช้ round(2) เพื่อปัดเศษทศนิยมให้ตรงกันก่อนเทียบ
                c1 = merged[f"{col}{suffix1}"].round(2)
                c2 = merged[f"{col}{suffix2}"].round(2)
                total_matches += (c1 == c2).sum()
            return total_matches
        except Exception:
            return 0

    # Execute comparisons
    s_yf_tw = calculate_match(df_yf, df_tw, "_yf", "_tw")
    score["yfinance"] += s_yf_tw
    score["twelvedata"] += s_yf_tw

    s_yf_tv = calculate_match(df_yf, df_tv, "_yf", "_tv")
    score["yfinance"] += s_yf_tv
    score["tradingview"] += s_yf_tv

    s_tw_tv = calculate_match(df_tw, df_tv, "_tw", "_tv")
    score["twelvedata"] += s_tw_tv
    score["tradingview"] += s_tw_tv

    print("\n===== SIMILARITY SCORE =====")
    print(score)

    # --- 5. Find Winner ---
    # กรองเอาเฉพาะ Source ที่มีข้อมูล (>0 records)
    valid_sources = {k: v for k, v in score.items() if not to_df(raw_data[k]["csv"]).empty}
    
    if valid_sources:
        # ถ้ามีคะแนน ให้เลือกตัวที่คะแนนมากสุด
        # ถ้าคะแนนเท่ากัน ให้เลือกตัวที่มี record count เยอะสุด
        best_source = max(valid_sources, key=lambda k: (valid_sources[k], raw_data[k]["count"]))
    else:
        # ถ้าไม่มีใครเหมือนกันเลย (score 0 หมด) ให้เลือกตัวที่มี record count เยอะสุด
        valid_counts = {k: raw_data[k]["count"] for k in raw_data if raw_data[k]["count"] > 0}
        if valid_counts:
            best_source = max(valid_counts, key=valid_counts.get)
        else:
            return f"# Error: Comparison failed for {symbol}\n", ""

    print(f"\n>>> BEST SOURCE: {best_source.upper()} <<<")

    # ส่งผลไป Telegram
    sent_to_telegram(report_message, score, best_source)

    # --- 6. Return Data ---
    return raw_data[best_source]["header"], raw_data[best_source]["csv"]


# ==========================================
# ✅ MAIN TOOL DEFINITION (For Agent)
# ==========================================

@tool
def get_stock_data(
    symbol: Annotated[str, "Ticker symbol of the company, e.g. AAPL, TSM"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """Retrieve stock price data (OHLCV) for a given ticker symbol.
    
    This tool compares data from multiple providers (Yahoo Finance, TwelveData, TradingView)
    and returns the most reliable dataset in CSV format.
    
    Args:
        symbol: Ticker symbol of the company.
        start_date: Start date string (YYYY-MM-DD).
        end_date: End date string (YYYY-MM-DD).
    Returns:
        str: A formatted CSV string containing the stock price data.
    """
    
    # เรียกฟังก์ชันเปรียบเทียบโดยตรง (Bypass Router เพื่อแก้ปัญหา Local/Config)
    header, csv_string = compare_stock_providers(symbol, start_date, end_date)
    
    return header + csv_string