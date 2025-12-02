import os
import sys
import pandas as pd
import requests
from typing import Annotated
from datetime import datetime
from langchain_core.tools import tool

# --- Import Provider Functions (ตรวจสอบ Path ให้ถูกต้อง) ---
from tradingagents.dataflows.y_finance import get_stock_stats_indicators_window
from tradingagents.dataflows.alpha_vantage_indicator import get_indicator
from tradingagents.dataflows.trading_view import get_tradingview_indicators

# ==========================================
# Helper Functions
# ==========================================

def compute_core_indicator_score(data_yf, data_av, data_tv, indicator, tolerance=0.01):
    """
    Compare data from different providers and score their similarity.
    """
    dict_yf, dict_av, dict_tv = {}, {}, {}

    # 1. Parse Yahoo Finance Data (list of tuples: (date_str, value))
    if data_yf:
        try:
            dict_yf = {str(d): float(v) for d, v in data_yf if v is not None}
        except Exception: pass

    # 2. Parse Alpha Vantage Data (list of tuples: (datetime_obj, value))
    if data_av:
        try:
            dict_av = {dt.strftime('%Y-%m-%d'): float(v) for dt, v in data_av if v is not None}
        except Exception: pass

    # 3. Parse TradingView Data (DataFrame)
    if isinstance(data_tv, pd.DataFrame) and not data_tv.empty:
        try:
            # ตรวจสอบว่ามี column datetime และ indicator ที่ต้องการไหม
            if 'datetime' in data_tv.columns and indicator in data_tv.columns:
                for _, row in data_tv.iterrows():
                    if pd.notna(row[indicator]):
                        dt_str = row['datetime'].strftime('%Y-%m-%d') if hasattr(row['datetime'], 'strftime') else str(row['datetime'])[:10]
                        dict_tv[dt_str] = float(row[indicator])
        except Exception: pass

    # Find intersection of dates (เฉพาะวันที่ที่มีข้อมูลครบอย่างน้อย 2 เจ้าถึงจะเทียบได้)
    all_dates = set(dict_yf.keys()) | set(dict_av.keys()) | set(dict_tv.keys())
    
    scores = {'yahoo': 0, 'alpha': 0, 'tv': 0}

    for date in sorted(all_dates):
        vals = {
            'yahoo': dict_yf.get(date), 
            'alpha': dict_av.get(date), 
            'tv': dict_tv.get(date)
        }
        
        # เปรียบเทียบทีละคู่ (เฉพาะคู่ที่มีค่าทั้งสองฝั่ง)
        pairs = [('yahoo', 'alpha'), ('yahoo', 'tv'), ('alpha', 'tv')]
        
        for src1, src2 in pairs:
            v1, v2 = vals[src1], vals[src2]
            if v1 is not None and v2 is not None:
                try:
                    # คำนวณความต่างสัมพัทธ์
                    diff = abs(v1 - v2)
                    denom = max(abs(v1), abs(v2))
                    if denom == 0: # กันหารด้วยศูนย์ (กรณีค่าเป็น 0 ทั้งคู่)
                        if diff == 0:
                            scores[src1] += 1
                            scores[src2] += 1
                    elif (diff / denom) <= tolerance:
                        scores[src1] += 1
                        scores[src2] += 1
                except Exception: pass

    # เลือก source ที่คะแนนสูงสุด
    max_score = max(scores.values()) if scores else 0
    best_sources = [k for k, v in scores.items() if v == max_score]
    
    # Fallback: ถ้าคะแนนเป็น 0 หมด ให้เลือกเจ้าที่มีข้อมูลเยอะสุด
    if max_score == 0:
        counts = {'yahoo': len(dict_yf), 'alpha': len(dict_av), 'tv': len(dict_tv)}
        max_count = max(counts.values())
        if max_count > 0:
            best_sources = [k for k, v in counts.items() if v == max_count]
        else:
            best_sources = ['alpha'] # Default สุดท้ายถ้าไม่มีข้อมูลเลย

    return scores, best_sources

def sent_to_telegram(report_message):
    """Send comparison result to Telegram bot."""
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    
    if not TOKEN or not CHAT_ID:
        return

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": report_message
    }

    # write text file
    with open("all_report_message.txt", "a", encoding='utf-8') as file:
        file.write(report_message + "\n")

    # try:
    #     requests.post(url, data=data, timeout=5)
    # except Exception as e:
    #     print(f"Telegram Error: {e}")

# ==========================================
# ✅ MAIN TOOL DEFINITION
# ==========================================

@tool
def get_indicators(
    symbol: str,
    indicator: str,
    curr_date: str,
    look_back_days: int,
) -> str:
    """
    Retrieve technical indicators for a given ticker symbol.
    
    This tool compares indicator values from multiple providers (Yahoo, Alpha Vantage, TradingView)
    to ensure accuracy and returns the most reliable dataset.
    
    Args:
        symbol (str): Ticker symbol (e.g., AAPL).
        indicator (str): Indicator code (e.g., 'rsi', 'macd', 'sma').
        curr_date (str): The current date for analysis (YYYY-MM-DD).
        look_back_days (int): Number of past days to retrieve data for.
        
    Returns:
        str: A formatted string containing the indicator data.
    """
    
    print(f"\n🚀 Fetching & Comparing Indicator '{indicator}' for {symbol}...")

    # 1. Fetch Data (Safely)
    result_str_yf, data_yf = "", []
    try:
        result_str_yf, data_yf = get_stock_stats_indicators_window(symbol, indicator, curr_date, look_back_days)
    except Exception as e:
        print(f"⚠️ Yahoo Finance Error: {e}")

    result_str_av, data_av = "", []
    try:
        result_str_av, data_av = get_indicator(symbol, indicator, curr_date, look_back_days)
    except Exception as e:
        print(f"⚠️ Alpha Vantage Error: {e}")

    result_str_tv, data_tv = "", pd.DataFrame()
    try:
        result_str_tv, data_tv = get_tradingview_indicators(symbol, indicator, curr_date, look_back_days)
    except Exception as e:
        print(f"⚠️ TradingView Error: {e}")

    # 2. Compute Scores
    scores, best_sources = compute_core_indicator_score(
        data_yf=data_yf,
        data_av=data_av,
        data_tv=data_tv,
        indicator=indicator,
        tolerance=0.01  # 1% tolerance
    )

    print(f"   Scores: {scores} => Best: {best_sources}")

    # 3. Send Report to Telegram (Optional)
    report_message = (
        f"📊 Indicator '{indicator}' Source Comparison for {symbol}:\n"
        f"Yahoo Finance Score: {scores.get('yahoo', 0)}\n"
        f"Alpha Vantage Score: {scores.get('alpha', 0)}\n"
        f"TradingView Score: {scores.get('tv', 0)}\n"
        f"🏆 Best Source: {', '.join([s.upper() for s in best_sources])}\n"
    )
    sent_to_telegram(report_message)

    # 4. Return Best Result
    # Priority: Alpha > Yahoo > TV (ถ้าคะแนนเท่ากัน หรืออยู่ในกลุ่ม best_sources)
    # แต่ต้องเช็คด้วยว่ามีข้อมูล (string ไม่ว่าง)
    
    if 'alpha' in best_sources and result_str_av:
        return result_str_av
    elif 'yahoo' in best_sources and result_str_yf:
        return result_str_yf
    elif 'tv' in best_sources and result_str_tv:
        return result_str_tv
    
    # Fallback logic (ถ้าตัวชนะไม่มีข้อมูล string ให้เอาตัวที่มี)
    if result_str_av: return result_str_av
    if result_str_yf: return result_str_yf
    if result_str_tv: return result_str_tv
    
    return f"No data found for indicator {indicator}"