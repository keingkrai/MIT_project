# -*- coding: utf-8 -*-
# indicators_source_picker_1mo_tv_av_yf.py

import os, json, sys, requests
from typing import Dict, List, Optional, Tuple, Literal
from datetime import datetime, timezone
import pandas as pd

# ================== PATHS ==================
BASE_DIR      = r"C:\TradingAgents_fail\data\indicators"
CSV_SERIES    = os.path.join(BASE_DIR, "{symbol}", "{source}_indicators_1mo.csv")
JSONL_SERIES  = os.path.join(BASE_DIR, "{symbol}", "{source}_indicators_1mo.jsonl")
JSONL_SUMMARY = os.path.join(BASE_DIR, "{symbol}", "indicator_source_decision_1mo.jsonl")

VERBOSE = True  # ตั้ง False เพื่อลด log

# ================== KEYS / TOL ==================
COMPARE_KEYS = ["close_50_sma","close_200_sma","close_10_ema","macd","rsi","boll_ub","boll_lb"]
INDICATOR_TOL = {
    "rsi":            {"abs": 0.25, "rel": 0.0},
    "macd":           {"abs": 0.005, "rel": 0.0},
    "close_10_ema":   {"abs": 0.03,  "rel": 6e-4},
    "close_50_sma":   {"abs": 0.04,  "rel": 6e-4},
    "close_200_sma":  {"abs": 0.06,  "rel": 6e-4},
    "boll_ub":        {"abs": 0.06,  "rel": 7e-4},
    "boll_lb":        {"abs": 0.06,  "rel": 7e-4},
}

def _log(*a):
    if VERBOSE: print(*a)

def _ensure_dir(path: str):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

def _save_csv(df: pd.DataFrame, path_fmt: str, **fmt) -> str:
    path = path_fmt.format(**fmt); _ensure_dir(path); df.to_csv(path, index=True); return path

def _save_series_jsonl(df: pd.DataFrame, path_fmt: str, **fmt) -> str:
    path = path_fmt.format(**fmt); _ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        for ts, row in df.iterrows():
            rec = {"date": ts.isoformat()}
            rec.update({k: (None if pd.isna(v) else float(v)) for k, v in row.items()})
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return path

def _append_jsonl_line(obj: Dict, path_fmt: str, **fmt) -> str:
    path = path_fmt.format(**fmt); _ensure_dir(path)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    return path

def _is_close(key: str, a: float, b: float) -> bool:
    cfg = INDICATOR_TOL.get(key, {"abs": 0.05, "rel": 1e-3})
    tol_abs, tol_rel = cfg["abs"], cfg["rel"]; diff = abs(a - b)
    return diff <= max(tol_abs, tol_rel * max(abs(a), abs(b), 1e-12))

def _align_on_dates(a: pd.DataFrame, b: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    if a.empty or b.empty: return a.iloc[0:0], b.iloc[0:0]
    idx = a.index.intersection(b.index)
    return a.loc[idx], b.loc[idx]

# ================== INDICATORS ==================
from ta.trend import EMAIndicator, SMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

def _compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["close_10_ema"]  = EMAIndicator(close=out["Close"], window=10).ema_indicator()
    out["close_50_sma"]  = SMAIndicator(close=out["Close"], window=50).sma_indicator()
    out["close_200_sma"] = SMAIndicator(close=out["Close"], window=200).sma_indicator()
    macd = MACD(close=out["Close"], window_slow=26, window_fast=12, window_sign=9)
    out["macd"]  = macd.macd()
    out["rsi"]   = RSIIndicator(close=out["Close"], window=14).rsi()
    bb = BollingerBands(close=out["Close"], window=20, window_dev=2)
    out["boll_ub"] = bb.bollinger_hband()
    out["boll_lb"] = bb.bollinger_lband()
    keep = ["Close"] + [k for k in COMPARE_KEYS if k in out.columns]
    return out[keep].dropna()

def _normalize_ohlcv_from_yf(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return df
    if isinstance(df.columns, pd.MultiIndex): df = df.copy(); df.columns = df.columns.droplevel(-1)
    ren = {c: c.capitalize() for c in df.columns}; df = df.rename(columns=ren)
    if "Adj close" in df.columns: df = df.rename(columns={"Adj close":"Adj Close"})
    return df

# ================== yfinance (1mo) ==================
def fetch_series_yfinance_1mo(symbol: str) -> pd.DataFrame:
    import yfinance as yf
    df = yf.download(symbol, period="60d", interval="1d", auto_adjust=False,
                     progress=False, group_by="column", threads=True)
    if df.empty: return pd.DataFrame()
    df = _normalize_ohlcv_from_yf(df)
    for c in ["Open","High","Low","Close"]:
        if c not in df.columns: return pd.DataFrame()
    df.index = pd.to_datetime(df.index, utc=True)
    df = df.dropna(subset=["Open","High","Low","Close"])
    # ตัดเฉพาะ ~30–35 วันล่าสุด
    df = df.loc[df.index >= (df.index.max() - pd.Timedelta(days=35))]
    return _compute_indicators(df)

# ================== Alpha Vantage (1mo) ==================
AV_BASE = "https://www.alphavantage.co/query"
def _av_get(function: str, params: dict, api_key: Optional[str] = None) -> dict:
    api_key = "7DJF0DNKIR9T1F9X"
    if not api_key: raise RuntimeError("ALPHAVANTAGE_API_KEY not set")
    p = {"function": function, "apikey": api_key, **params}
    r = requests.get(AV_BASE, params=p, timeout=30); r.raise_for_status()
    data = r.json()
    if "Error Message" in data: raise RuntimeError(f"AlphaVantage error: {data['Error Message']}")
    if "Note" in data: raise RuntimeError(f"AlphaVantage note: {data['Note']}")
    return data

def _parse_av_ts(data: dict) -> pd.DataFrame:
    ts = data.get("Time Series (Daily)") or data.get("Time Series (Daily) ") or {}
    if not ts: return pd.DataFrame()
    df = pd.DataFrame.from_dict(ts, orient="index").rename(columns={
        "1. open":"Open","2. high":"High","3. low":"Low","4. close":"Close","6. volume":"Volume"
    })
    for c in ["Open","High","Low","Close","Volume"]:
        if c in df.columns: df[c] = pd.to_numeric(df[c], errors="coerce")
    df.index = pd.to_datetime(df.index, utc=True)
    df = df.sort_index()
    df = df.loc[df.index >= (df.index.max() - pd.Timedelta(days=35))]
    return df.dropna(subset=["Open","High","Low","Close"])

def fetch_series_alphavantage_1mo(symbol: str) -> pd.DataFrame:
    for fn in ["TIME_SERIES_DAILY_ADJUSTED", "TIME_SERIES_DAILY"]:
        try:
            data = _av_get(fn, {"symbol": symbol, "outputsize":"compact"})
            df = _parse_av_ts(data)
            if len(df):
                _log(f"[AV] used {fn}, rows={len(df)}")
                return _compute_indicators(df)
        except Exception as e:
            _log(f"[AV] {fn} fail: {e}")
            continue
    return pd.DataFrame()

# ================== TradingView snapshot (latest only) ==================
def fetch_tradingview_snapshot(symbol: str) -> Dict[str, float]:
    """
    ใช้ tradingview_ta ดึงค่าล่าสุดของอินดิเคเตอร์ (ไม่มีซีรีส์)
    """
    try:
        from tradingview_ta import TA_Handler, Interval
        h = TA_Handler(symbol=symbol, screener="america", exchange="NASDAQ",
                       interval=Interval.INTERVAL_1_DAY)
        ind = (h.get_analysis().indicators) or {}
        def _sf(x):
            try: return float(x) if x is not None else None
            except: return None
        snap = {
            "close_50_sma": _sf(ind.get("SMA50") or ind.get("sma50")),
            "close_200_sma": _sf(ind.get("SMA200") or ind.get("sma200")),
            "close_10_ema": _sf(ind.get("EMA10") or ind.get("ema10")),
            "macd": _sf(ind.get("MACD.macd") or ind.get("macd")),
            "rsi": _sf(ind.get("RSI") or ind.get("RSI[14]") or ind.get("rsi")),
            "boll_ub": _sf(ind.get("BB.upper") or ind.get("BOLL_UPPER")),
            "boll_lb": _sf(ind.get("BB.lower") or ind.get("BOLL_LOWER")),
        }
        return {k:v for k,v in snap.items() if v is not None}
    except Exception as e:
        _log(f"[TV] snapshot fail: {e}")
        return {}

# ================== SCORING ==================
def score_agreement_span(df_a: pd.DataFrame, df_b: pd.DataFrame) -> Dict:
    A, B = _align_on_dates(df_a, df_b)
    if A.empty or B.empty: return {"overlap_days": 0, "per_key": {}, "overall": 0.0}
    per_key, hits_all = {}, []
    for k in COMPARE_KEYS:
        if k not in A.columns or k not in B.columns: per_key[k] = 0.0; continue
        flags = [
            _is_close(k, float(aa), float(bb))
            for aa, bb in zip(A[k].astype(float), B[k].astype(float))
            if pd.notna(aa) and pd.notna(bb)
        ]
        per_key[k] = (sum(flags)/len(flags)) if flags else 0.0
        hits_all.extend(flags)
    overall = (sum(hits_all)/len(hits_all)) if hits_all else 0.0
    return {"overlap_days": len(A), "per_key": per_key, "overall": overall}

def score_latest_vs_tv(df: pd.DataFrame, tv_snap: Dict[str, float]) -> float:
    if df.empty or not tv_snap: return 0.0
    row = df.iloc[-1]; flags = []
    for k in COMPARE_KEYS:
        a = row.get(k, None); b = tv_snap.get(k, None)
        if pd.isna(a) or (b is None): continue
        flags.append(_is_close(k, float(a), float(b)))
    return (sum(flags)/len(flags)) if flags else 0.0

def _usable_rows(df: pd.DataFrame) -> int:
    cols = [c for c in COMPARE_KEYS if c in df.columns]
    return len(df.dropna(subset=cols)) if cols else 0

# ================== ORCHESTRATOR ==================
def decide_indicator_source_1mo(
    symbol: str,
    *,
    return_as: Literal["dataframe","records"] = "records",
) -> Dict:
    """
    ดึงซีรีส์อินดิเคเตอร์ “ย้อนหลัง ~1 เดือน” จาก Alpha Vantage และ yfinance
    + ใช้ TradingView (สแนปชอตล่าสุด) เพื่อช่วยชี้ขาด
    แล้วเลือก ‘แหล่งเดียว’ พร้อมบันทึก CSV/JSONL/สรุป JSONL
    """
    symbol = symbol.upper()

    av = fetch_series_alphavantage_1mo(symbol)
    yf = fetch_series_yfinance_1mo(symbol)
    tv_snap = fetch_tradingview_snapshot(symbol)

    sources = {name: df for name, df in [("alphavantage", av), ("yfinance", yf)] if not df.empty}
    if not sources:
        raise RuntimeError("ไม่พบข้อมูลอินดิเคเตอร์ (1 เดือน) จาก Alpha Vantage และ yfinance")

    pair_scores = {}
    chosen_name, chosen_df = None, None

    if len(sources) == 1:
        chosen_name, chosen_df = next(iter(sources.items()))
    else:
        # AV vs YF
        pair_scores["alphavantage_vs_yfinance"] = score_agreement_span(av, yf)
        # คะแนนกับ TV (ล่าสุด)
        av_tv = score_latest_vs_tv(av, tv_snap)
        yf_tv = score_latest_vs_tv(yf, tv_snap)

        # เลือกโดย: (1) overall score AV↔YF สูง → ใช้แหล่งที่ใกล้ TV กว่า
        # ถ้าเสมอ → ใช้ usable_rows มากกว่า
        overall = pair_scores["alphavantage_vs_yfinance"]["overall"]

        # baseline: ใช้ usable rows เป็นตัวชี้ขาดหลัก
        def usable(df): return _usable_rows(df)
        # tie-break ด้วยใกล้ TV
        pick_score_av = (overall, av_tv, usable(av))
        pick_score_yf = (overall, yf_tv, usable(yf))

        # ถ้า TV snapshot ไม่มี ก็เทียบ usable_rows อย่างเดียว
        key_fn = (lambda x: (x[2])) if not tv_snap else (lambda x: (x[1], x[2]))
        if key_fn(pick_score_yf) >= key_fn(pick_score_av):
            chosen_name, chosen_df = "yfinance", yf
        else:
            chosen_name, chosen_df = "alphavantage", av

        pair_scores["latest_vs_tv"] = {"alphavantage": av_tv, "yfinance": yf_tv}

    # บันทึก
    now_iso = datetime.now(timezone.utc).isoformat()
    csv_path   = _save_csv(chosen_df,   CSV_SERIES,   symbol=symbol, source=chosen_name)
    jsonl_path = _save_series_jsonl(chosen_df, JSONL_SERIES, symbol=symbol, source=chosen_name)

    summary_line = {
        "timestamp": now_iso,
        "symbol": symbol,
        "chosen_source": chosen_name,
        "compare_keys": COMPARE_KEYS,
        "tolerance": INDICATOR_TOL,
        "rows": len(chosen_df),
        "scores": pair_scores,
        "paths": {"csv": csv_path, "jsonl": jsonl_path},
        "notes": {
            "av_has_data": not av.empty,
            "yf_has_data": not yf.empty,
            "tv_snapshot": bool(tv_snap),
        }
    }
    summary_path = _append_jsonl_line(summary_line, JSONL_SUMMARY, symbol=symbol)

    series_out = (
        chosen_df if return_as == "dataframe"
        else [{"date": ts.isoformat(), **{k: (None if pd.isna(v) else float(v)) for k, v in row.items()}}
              for ts, row in chosen_df.iterrows()]
    )

    return {
        "symbol": symbol,
        "timestamp": now_iso,
        "chosen_source": chosen_name,
        "paths": {
            "chosen_csv": csv_path,
            "chosen_jsonl": jsonl_path,
            "summary_jsonl": summary_path,
        },
        "scores": pair_scores,
        "series": series_out,
    }

# ============== CLI ==============
if __name__ == "__main__":
    sym = sys.argv[1] if len(sys.argv) >= 2 else "NVDA"
    res = decide_indicator_source_1mo(sym, return_as="records")
    print("Chosen:", res["chosen_source"])
    print("Rows:", len(res["series"]))
    print("Saved CSV:", res["paths"]["chosen_csv"])
    print("Saved JSONL:", res["paths"]["chosen_jsonl"])
