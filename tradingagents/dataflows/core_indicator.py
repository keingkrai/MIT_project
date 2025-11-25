import os
import sys
from turtle import pd
from typing import Annotated

import requests
from tradingagents.dataflows.y_finance import get_stock_stats_indicators_window
from tradingagents.dataflows.alpha_vantage_indicator import get_indicator
from tradingagents.dataflows.trading_view import get_tradingview_indicators

from datetime import datetime

def compute_core_indicator_score(data_yf, data_av, data_tv, indicator, tolerance=0.01):
    """
    data_yf: list of (date_str, value_str)
    data_av: list of (datetime_obj, value_str)
    data_tv: pandas DataFrame with 'datetime' and indicator column
    tolerance: relative difference threshold
    """
    # 1. แปลงข้อมูลเป็น dict
    dict_yf = {d: float(v) for d, v in data_yf}
    dict_av = {dt.strftime('%Y-%m-%d'): float(v) for dt, v in data_av}
    dict_tv = {dt.strftime('%Y-%m-%d'): float(v) for dt, v in zip(data_tv['datetime'], data_tv[indicator])}

    all_dates = set(dict_yf.keys()) & set(dict_av.keys()) & set(dict_tv.keys())
    
    scores = {'yahoo': 0, 'alpha': 0, 'tv': 0}

    for date in sorted(all_dates):
        vals = {'yahoo': dict_yf[date], 'alpha': dict_av[date], 'tv': dict_tv[date]}
        
        # เปรียบเทียบกันทีละคู่
        for src1, src2 in [('yahoo','alpha'), ('yahoo','tv'), ('alpha','tv')]:
            v1, v2 = vals[src1], vals[src2]
            if abs(v1-v2)/max(v1,v2) <= tolerance:
                scores[src1] += 1
                scores[src2] += 1

    # เลือก source ที่ max score
    max_score = max(scores.values())
    best_sources = [k for k, v in scores.items() if v == max_score]

    return scores, best_sources

def sent_to_telegram(report_message):
    """Send comparison result to Telegram bot."""
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    MESSAGE = report_message
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": MESSAGE
    }
    resp = requests.post(url, data=data)
    # print(resp.json())

def get_core_indicator(
    symbol: str,
    indicator: str,
    curr_date: str,
    look_back_days: int,
) -> str:
    # result_str_yf, data_yf = get_stock_stats_indicators_window(symbol, indicator, curr_date, look_back_days)
    # # print(f"\n\n=== Yahoo Finance ===\n{data_yf}")
    # result_str_av, data_av = get_indicator(symbol, indicator, curr_date, look_back_days)
    # # print(f"\n\n=== Alpha Vantage ===\n{data_av}")
    # result_str_tv, data_tv = get_tradingview_indicators(symbol, indicator, curr_date, look_back_days)
    # # print(f"\n\n=== TradingView ===\n{data_tv}")

    # scores, best_sources = compute_core_indicator_score(
    #     data_yf=data_yf,
    #     data_av=data_av,
    #     data_tv=data_tv,
    #     indicator=indicator,
    #     tolerance=0.01
    # )

    # print(f"\n\n=== Scores ===\n{scores}\nBest sources: {best_sources}")

    # try check null result

    try:
        result_str_yf, data_yf = get_stock_stats_indicators_window(symbol, indicator, curr_date, look_back_days)
    except Exception as e:
        result_str_yf, data_yf = "", []
        print(f"Yahoo Finance error for indicator '{indicator}': {e}")

    try:
        result_str_av, data_av = get_indicator(symbol, indicator, curr_date, look_back_days)
    except Exception as e:
        result_str_av, data_av = "", []
        print(f"Alpha Vantage error for indicator '{indicator}': {e}")

    try:
        result_str_tv, data_tv = get_tradingview_indicators(symbol, indicator, curr_date, look_back_days)
    except Exception as e:
        result_str_tv, data_tv = "", pd.DataFrame()
        print(f"TradingView error for indicator '{indicator}': {e}")

    # count score for each provider
    scores, best_sources = compute_core_indicator_score(
        data_yf=data_yf,
        data_av=data_av,
        data_tv=data_tv,
        indicator=indicator,
        tolerance=0.001
    )

    # max score provider
    print(f"\n\n=== Scores ===\n{scores}\nBest sources: {best_sources}")

    # send to telegram
    report_message = (
        f"Stock Indicator Data Source Comparison Result for {symbol} - {indicator}:\n\n"
        f"Yahoo Finance Score: {scores.get('yahoo', 0)}\n"
        f"Alpha Vantage Score: {scores.get('alpha', 0)}\n"
        f"TradingView Score: {scores.get('tv', 0)}\n\n"
        f"Best Sources: {', '.join(best_sources)}"
    )
    print("Sending report to Telegram...")
    print(report_message)
    sent_to_telegram(report_message)

    # sys.exit("Program stopped by user request")

    # return max score provider result
    if 'alpha' in best_sources and result_str_av is not None:
        return result_str_av
    elif 'yahoo' in best_sources and result_str_yf is not None:
        return result_str_yf
    elif 'tv' in best_sources and result_str_tv is not None:
        return result_str_tv
    else:
        return result_str_av