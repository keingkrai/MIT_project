import os
from tradingagents.dataflows.y_finance import get_YFin_data_online
from tradingagents.dataflows.alpha_vantage_stock import get_alpha_vantage_stock
from tradingagents.dataflows.trading_view import get_TV_data_online
from tradingagents.dataflows.twelve_data import get_twelvedata_stock
import sys
import pandas as pd
import io
import re
import requests

def get_stock_data(
    symbol: str,
    start_date: str,
    end_date: str,
) -> str:
    """Retrieve stock price data (OHLCV) for a given ticker symbol.

    Args:
        symbol: Ticker symbol of the company, e.g. AAPL, TSM
        start_date: Start date in yyyy-mm-dd format
        end_date: End date in yyyy-mm-dd format
    Returns:
        A formatted dataframe containing the stock price data for the specified ticker symbol in the specified date range.
    """
    # print("\n\n\nDEBUG:get_stock_data")

    header, csv_string = compare_stock_providers(symbol, start_date, end_date)

    # print("\n\n\nFINISH DEBUG:get_stock_data")

    # sys.exit("Program stopped by user request")

    return header + csv_string

def compare_stock_providers(symbol, start_date, end_date):

    # --- call each provider ---
    header_yf, yfin_csv = get_YFin_data_online(symbol, start_date, end_date)
    # header_av, alpha_csv = get_alpha_vantage_stock(symbol, start_date, end_date)
    header_tw , tw_csv = get_twelvedata_stock(symbol, start_date, end_date)
    header_tv, tv_csv = get_TV_data_online(symbol, start_date, end_date)

    # --- extract total records from headers ---
    rec_yf = extract_record_count(header_yf)
    # rec_av = extract_record_count(header_av)
    rec_tw = extract_record_count(header_tw)
    rec_tv = extract_record_count(header_tv)

    print("\n===== HEADERS =====")
    print("YFinance:", header_yf)
    # print("AlphaVantage:", header_av)
    print("TwelveData:", header_tw)
    print("TradingView:", header_tv)

    print("\n===== TOTAL RECORDS CHECK =====")
    print(f"YFinance:      {rec_yf}")
    # print(f"AlphaVantage:  {rec_av}")
    print(f"TwelveData:    {rec_tw}")
    print(f"TradingView:   {rec_tv}")

    if rec_yf == rec_tw == rec_tv:
        print("\n✔ All sources have the same number of records.")
    else:
        print("\n❌ Record count mismatch!")
        # if rec_yf != rec_av: print(f"  - YFinance vs AlphaVantage differ: {rec_yf} vs {rec_av}")
        if rec_yf != rec_tw: print(f"  - YFinance vs TwelveData differ: {rec_yf} vs {rec_tw}")
        if rec_yf != rec_tv: print(f"  - YFinance vs TradingView differ: {rec_yf} vs {rec_tv}")
        # if rec_av != rec_tv: print(f"  - AlphaVantage vs TradingView differ: {rec_av} vs {rec_tv}")
        if rec_tw != rec_tv:print(f"  - TwelveData vs TradingView differ: {rec_tw} vs {rec_tv}")

    # --- Report message ---
    report_message = ""

    report_message += "===== TOTAL RECORDS CHECK =====\n"
    report_message += f"YFinance:      {rec_yf}\n"
    # report_message += f"AlphaVantage:  {rec_av}\n"
    report_message += f"TwelveData:    {rec_tw}\n"
    report_message += f"TradingView:   {rec_tv}\n\n"

    if rec_yf == rec_tw == rec_tv:
        report_message += "✔ All sources have the same number of records.\n"
    else:
        report_message += "❌ Record count mismatch!\n"
        if rec_yf != rec_tw:
            report_message += f"  - YFinance vs TwelveData differ: {rec_yf} vs {rec_tw}\n"
        if rec_yf != rec_tv:
            report_message += f"  - YFinance vs TradingView differ: {rec_yf} vs {rec_tv}\n"
        if rec_tw != rec_tv:
            report_message += f"  - TwelveData vs TradingView differ: {rec_tw} vs {rec_tv}\n"

    # --- convert to DataFrame ---
    df_yf = to_df(yfin_csv)
    # df_av = to_df(alpha_csv)
    df_tw = to_df(tw_csv)
    df_tv = to_df(tv_csv)

    # --- Align by Date ---
    df_yf["Date"] = pd.to_datetime(df_yf["Date"])
    df_tw["Date"] = pd.to_datetime(df_tw["Date"])
    df_tv["Date"] = pd.to_datetime(df_tv["Date"])

    merged = df_yf.merge(df_tw, on="Date", suffixes=("_yf", "_tw"))
    merged = merged.merge(df_tv, on="Date")
    merged = merged.rename(columns={
        "Open": "Open_tv",
        "High": "High_tv",
        "Low": "Low_tv",
        "Close": "Close_tv",
        "Volume": "Volume_tv",
    })

    print("\n===== MERGED (TAIL) =====")
    print(merged.tail())

    # --- compute differences ---
    # merged["diff_close_yf_av"] = merged["Close_yf"] - merged["Close_av"]
    # merged["diff_close_yf_tv"] = merged["Close_yf"] - merged["Close_tv"]
    # merged["diff_close_av_tv"] = merged["Close_av"] - merged["Close_tv"]

    # print("\n===== DIFFERENCE SUMMARY =====")
    # print(merged[[
    #     "Date",
    #     "diff_close_yf_av",
    #     "diff_close_yf_tv",
    #     "diff_close_av_tv"
    # ]].tail())

    # --- scoring for similarity ---
    sources = ["yf", "tw", "tv"]
    score = {"yf": 0, "tv": 0, "tw": 0}

    compare_cols = ["Open", "High", "Low", "Close", "Volume"]

    for col in compare_cols:
        col_yf = f"{col}_yf"
        col_tv = f"{col}_tv"
        col_tw = f"{col}_tw"

        # 1) YF vs TW
        mask_yf_tw = merged[col_yf] == merged[col_tw]
        score["yf"] += mask_yf_tw.sum()
        score["tw"] += mask_yf_tw.sum()

        # 2) YF vs TV
        mask_yf_tv = merged[col_yf] == merged[col_tv]
        score["yf"] += mask_yf_tv.sum()
        score["tv"] += mask_yf_tv.sum()

        # 3) TW vs TV
        mask_tw_tv = merged[col_tw] == merged[col_tv]
        score["tw"] += mask_tw_tv.sum()
        score["tv"] += mask_tw_tv.sum()

    print("\n===== SIMILARITY SCORE =====")
    print(score)

    # --- find winner ---
    best_source = max(score, key=score.get)
    print(f"\n>>> BEST SOURCE: {best_source.upper()} <<<")

    # --- send to telegram ---
    sent_to_telegram(report_message, score, best_source)

    # --- return data from the best source ---
    if best_source == "yf":
        return header_yf, yfin_csv
    elif best_source == "tw":
        return header_tw, tw_csv
    elif best_source == "tv":
        return header_tv, tv_csv
    else:
        return header_tv, tv_csv
    

def to_df(csv_string: str) -> pd.DataFrame:
    """Convert CSV string to pandas DataFrame."""
    return pd.read_csv(io.StringIO(csv_string))

def extract_record_count(header: str) -> int:
    """Extract 'Total records: XXX' from header."""
    match = re.search(r"Total records:\s*(\d+)", header)
    if match:
        return int(match.group(1))
    return None

def sent_to_telegram(report_message, score: dict, best_source: str):
    """Send comparison result to Telegram bot."""
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    MESSAGE = f"Stock Data Source Comparison Result:\n\n" \
              f"{report_message}"\
              f"\n===== SIMILARITY SCORE =====\n"\
              f"YFinance Score: {score['yf']}\n" \
              f"AlphaVantage Score: {score['av']}\n" \
              f"TradingView Score: {score['tv']}\n\n" \
              f"Best Source: {best_source.upper()}"
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": MESSAGE
    }

    resp = requests.post(url, data=data)
    print(resp.json())