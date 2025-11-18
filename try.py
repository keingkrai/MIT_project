from langchain_core.tools import tool
from typing import Annotated
from tradingagents.dataflows.interface import route_to_vendor

from dotenv import load_dotenv

from tradingagents.dataflows.y_finance import get_YFin_data_online

from tradingagents.dataflows.alpha_vantage import get_stock as get_alpha_vantage_stock

from tradingagents.dataflows.local import fetch_bsky_stock_posts, yfinance_get_company_news, reddit_get_company_news, finnhub_get_company_news, get_world_news_yf, fetch_reddit_world_news, get_tradingview_indicators, get_yfin_indicators_online, get_twelve_data_indicator, fetch_and_choose, get_finnhub_general_news

from datetime import datetime, timezone, timedelta
# โหลดค่าจากไฟล์ .env
load_dotenv()

# get stock price

# yfinance online
# print(get_YFin_data_online("AAPL", "2024-11-14", "2025-11-14"))

# print("--------------- alpha_vantage ---------------")
# print(get_tradingview_indicators("AAPL"))

# print("--------------- yfinance ---------------")
# print(get_yfin_indicators_online("AAPL"))

# print("--------------- twelve data ---------------")
# print(get_twelve_data_indicator("AAPL"))

# print("--------------- compare and pick 2 of 3 ---------------")
# print(fetch_and_choose("AAPL", as_markdown=True))


#----------------------------- get news ------------------------------
#--------------- finnhub news global ---------------
# items, _ = get_finnhub_general_news(output="df", max_pages=2)
# print(items)

#--------------- reddit world news ---------------
# test = fetch_reddit_world_news(per_sub_limit=30, time_filter="day")
# print(test)

#--------------- yfinance world news ---------------
# test2 = get_world_news_yf()
# print(test2)

#--------------- finn news stock---------------
# test3 = finnhub_get_company_news("NVDA", limit=50)
# print(test3)

# ----------------------------- reddit posts news ------------
# q = 'AAPL'
# items = reddit_get_company_news(query=q)

# ----------------------------- stock y-finance news ------------
q = 'AAPL'
# f = fetch_company_news_yfinance(symbol=q)
# print(f)

# yfinance_get_company_news(symbol=q)

# ----------------------------- bluesky posts ------------
posts = fetch_bsky_stock_posts(symbol=q)
print(posts)