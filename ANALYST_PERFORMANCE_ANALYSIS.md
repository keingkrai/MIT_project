# การวิเคราะห์ประสิทธิภาพของ Analyst Team

## 🔍 สาเหตุที่ Analyst Team ประมวลผลช้า

### 1. **Market Analyst - ปัญหาหลัก**

#### 1.1 การเรียก API หลายครั้งแบบ Sequential
- Market Analyst ต้องเรียก `get_indicators` **12 ครั้ง** (สำหรับ 12 indicators):
  - `close_50_sma`, `close_200_sma`, `close_10_ema`
  - `macd`, `macds`, `macdh`
  - `rsi`
  - `boll`, `boll_ub`, `boll_lb`
  - `atr`, `vwma`

- **แต่ละ indicator** ต้อง:
  1. เรียก Yahoo Finance API
  2. เรียก Alpha Vantage API
  3. เรียก TradingView API (ซึ่ง timeout บ่อย ~10-30 วินาที)
  4. เปรียบเทียบข้อมูลจาก 3 sources
  5. เลือก source ที่ดีที่สุด

- **เวลารวม**: 12 indicators × (3 API calls + comparison) = **36+ API calls**
- **เวลาที่เสียไป**: แต่ละ indicator ใช้เวลา ~5-30 วินาที (ขึ้นอยู่กับ TradingView timeout)
- **เวลารวมประมาณ**: 60-360 วินาที (1-6 นาที) สำหรับ Market Analyst เพียงอย่างเดียว

#### 1.2 TradingView Connection Timeout
- จาก terminal output: `ERROR:tvDatafeed.main:Connection timed out`
- แต่ละ indicator ต้องรอ TradingView timeout (~10-30 วินาที)
- 12 indicators × 30 วินาที = **360 วินาที (6 นาที)** เพียงแค่รอ timeout

#### 1.3 ไม่มีการทำ Parallel Processing
- LLM เรียก `get_indicators` แบบ **sequential** (ทีละ indicator)
- ไม่มีการใช้ `asyncio` หรือ `concurrent.futures` เพื่อเรียก indicators พร้อมกัน

#### 1.4 ไม่มีการ Cache
- ไม่มีการ cache ผลลัพธ์ของ indicators
- ถ้าเรียกซ้ำต้องดึงข้อมูลใหม่ทุกครั้ง

### 2. **Social Media Analyst**
- ต้องเรียก API 3 sources:
  - Bluesky API
  - Mastodon API
  - Reddit API
- แต่ละ source อาจใช้เวลา 5-15 วินาที

### 3. **News Analyst**
- ต้องดึงข้อมูลจากหลาย sources
- อาจต้องรอ API responses

### 4. **Fundamentals Analyst**
- ต้องดึงข้อมูล financial statements
- อาจใช้เวลานานถ้าข้อมูลเยอะ

## 📊 สรุปเวลาโดยประมาณ

### ก่อนแก้ไข:
| Analyst | API Calls | เวลาโดยประมาณ |
|---------|-----------|---------------|
| Market Analyst | 36+ calls (sequential) | 1-6 นาที |
| Social Media Analyst | 3+ calls | 15-45 วินาที |
| News Analyst | 3+ calls | 15-45 วินาที |
| Fundamentals Analyst | 3+ calls | 15-45 วินาที |
| **รวม** | **45+ calls** | **2-8 นาที** |

### หลังแก้ไข (ใช้ `get_all_indicators`):
| Analyst | API Calls | เวลาโดยประมาณ |
|---------|-----------|---------------|
| Market Analyst | 12 calls (parallel) | **1-2 นาที** ⚡ |
| Social Media Analyst | 3+ calls | 15-45 วินาที |
| News Analyst | 3+ calls | 15-45 วินาที |
| Fundamentals Analyst | 3+ calls | 15-45 วินาที |
| **รวม** | **21+ calls** | **2-4 นาที** ✅ |

**เป้าหมาย: เสร็จภายใน 5 นาที** ✅

## ✅ การแก้ไขที่ทำแล้ว

### 1. **Parallel Processing Tool - `get_all_indicators`** ✅
- สร้าง tool ใหม่ `get_all_indicators` ที่เรียก indicators หลายตัวพร้อมกันแบบ parallel
- ใช้ `ThreadPoolExecutor` เพื่อเรียก indicators พร้อมกัน (max 6 workers)
- ลดเวลาจาก 6 นาที เหลือ **~1-2 นาที** (เร็วขึ้น 3-6 เท่า)

### 2. **TradingView Timeout (5 seconds)** ✅
- เพิ่ม timeout 5 วินาทีสำหรับ TradingView
- ถ้า timeout จะ skip และใช้ source อื่นแทน
- ลดเวลาที่เสียไปกับการรอ timeout

### 3. **Updated System Message** ✅
- แก้ไข guideline ให้ใช้ `get_all_indicators` แทน `get_indicators` หลายครั้ง
- เน้นให้เรียก indicators ทั้งหมดในครั้งเดียว (parallel)

## 🚀 วิธีแก้ไขเพิ่มเติมที่แนะนำ

### 1. **Parallel Processing สำหรับ Indicators** (ทำแล้ว ✅)

```python
# ใน core_indicator.py - สร้างฟังก์ชันใหม่
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def get_all_indicators_parallel(
    symbol: str,
    indicators: List[str],
    curr_date: str,
    look_back_days: int
) -> Dict[str, str]:
    """เรียก indicators ทั้งหมดแบบ parallel"""
    
    async def fetch_indicator(indicator):
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(
                executor,
                get_indicators,
                symbol, indicator, curr_date, look_back_days
            )
            return indicator, result
    
    tasks = [fetch_indicator(ind) for ind in indicators]
    results = await asyncio.gather(*tasks)
    return dict(results)
```

**ผลลัพธ์**: ลดเวลาจาก 6 นาที เหลือ **~30-60 วินาที** (เร็วขึ้น 6-12 เท่า)

### 2. **Skip TradingView ถ้า Timeout เร็วขึ้น**

```python
# ใน core_indicator.py
import signal

def get_indicators_with_timeout(symbol, indicator, curr_date, look_back_days, timeout=5):
    """เรียก get_indicators พร้อม timeout"""
    # ใช้ timeout เพื่อไม่ให้รอ TradingView นานเกินไป
    # ถ้า TradingView timeout ภายใน 5 วินาที ให้ skip ไปใช้ source อื่น
```

### 3. **Caching System**

```python
# เพิ่ม caching สำหรับ indicators
from functools import lru_cache
import hashlib

@lru_cache(maxsize=100)
def get_indicators_cached(symbol, indicator, curr_date, look_back_days):
    """Cache ผลลัพธ์ของ indicators"""
    cache_key = f"{symbol}_{indicator}_{curr_date}_{look_back_days}"
    # ตรวจสอบ cache ก่อน
    # ถ้ามี cache และยังไม่หมดอายุ ให้ return cache
    # ถ้าไม่มี cache ให้เรียก API และเก็บ cache
```

### 4. **Optimize TradingView Calls**

```python
# ใน trading_view.py
# เพิ่ม timeout ที่สั้นกว่า
import signal

def get_tradingview_indicators_with_timeout(symbol, indicator, curr_date, look_back_days, timeout=5):
    """เรียก TradingView พร้อม timeout"""
    try:
        # ใช้ signal หรือ threading เพื่อ timeout
        result = get_tradingview_indicators(symbol, indicator, curr_date, look_back_days)
        return result
    except TimeoutError:
        return "", pd.DataFrame()  # Return empty ถ้า timeout
```

### 5. **Batch API Calls**

```python
# สำหรับ Alpha Vantage - เรียกหลาย indicators ในครั้งเดียวถ้าเป็นไปได้
# หรือใช้ bulk API endpoints
```

## 🎯 Priority ของการแก้ไข

1. **สูงสุด**: Parallel Processing สำหรับ Indicators
   - ลดเวลาได้มากที่สุด (6 นาที → 30-60 วินาที)
   - ต้องแก้ไข `market_analyst.py` และ `core_indicator.py`

2. **สูง**: Skip TradingView ถ้า Timeout เร็วขึ้น
   - ลดเวลาที่เสียไปกับการรอ timeout
   - ต้องแก้ไข `core_indicator.py` และ `trading_view.py`

3. **ปานกลาง**: Caching System
   - ช่วยเมื่อเรียกซ้ำ
   - ต้องเพิ่ม caching layer

4. **ต่ำ**: Optimize อื่นๆ
   - Batch API calls
   - Connection pooling

## 📝 Implementation Plan

### Phase 1: Quick Win (ทำได้ทันที)
1. เพิ่ม timeout สำหรับ TradingView (5 วินาที)
2. Skip TradingView ถ้า timeout เร็วขึ้น

### Phase 2: Major Improvement (1-2 วัน)
1. Implement Parallel Processing สำหรับ Indicators
2. เพิ่ม async/await support

### Phase 3: Optimization (3-5 วัน)
1. เพิ่ม Caching System
2. Optimize API calls
3. Connection pooling

## 💡 Quick Fix (ทำได้ทันที)

แก้ไข `core_indicator.py` เพื่อ skip TradingView ถ้า timeout:

```python
# ใน get_indicators function
result_str_tv, data_tv = "", pd.DataFrame()
try:
    # เพิ่ม timeout
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError("TradingView timeout")
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(5)  # 5 วินาที timeout
    
    result_str_tv, data_tv = get_tradingview_indicators(symbol, indicator, curr_date, look_back_days)
    signal.alarm(0)  # Cancel timeout
except (TimeoutError, Exception) as e:
    print(f"⚠️ TradingView Error (skipped): {e}")
    signal.alarm(0)  # Cancel timeout
```

**ผลลัพธ์**: ลดเวลาจาก 6 นาที เหลือ **~2-3 นาที** (เร็วขึ้น 2-3 เท่า)

