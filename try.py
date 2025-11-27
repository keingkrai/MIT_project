from langchain_core.tools import tool
from typing import Annotated
from tradingagents.dataflows.interface import route_to_vendor

from dotenv import load_dotenv



from tradingagents.dataflows.local import (
    
    #fundamental data
    pick_fundamental_source, 
    
    #globalnews data
    fetch_finnhub_world_news, 
    get_world_news_yf,
    fetch_reddit_world_news,
    
    #company news data
    yfinance_get_company_news, 
    reddit_get_company_news, 
    finnhub_get_company_news,
    alphavantage_get_company_news,
    
    #social media posts data 
    fetch_reddit_symbol_top_praw, 
    fetch_mastodon_stock_posts, 
    fetch_bsky_stock_posts, 
    
    #indicators data
    get_tradingview_indicators, 
    get_yfin_indicators_online, 
    get_twelve_data_indicator, 
    fetch_and_choose
    
    )
from datetime import datetime, timezone, timedelta
from tradingagents.dataflows.core_stock_price import get_stock_data
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
#print(fetch_and_choose("AAPL"))


#----------------------------- get news ------------------------------
#--------------- finnhub news global ---------------
# items, _ = get_finnhub_general_news(output="df", max_pages=2)
# print(items)

#--------------- reddit world news ---------------
# test = fetch_reddit_world_news()
# print(test)

#--------------- yfinance world news ---------------
# test2 = get_world_news_yf()
# print(test2)

# e = fetch_finnhub_world_news()
# print(e)

#--------------- finn news stock---------------
# test3 = finnhub_get_company_news("NVDA")
# print(test3)

# ----------------------------- reddit posts news ------------
q = 'RBLX'
# items = reddit_get_company_news(query=q)

# ----------------------------- stock y-finance news ------------
# q = 'AAPL'
# f = fetch_company_news_yfinance(symbol=q)
# print(f)

# yfinance_get_company_news(q)
# alphavantage_get_company_news(q)
# ----------------------------- bluesky posts ------------
# posts = fetch_bsky_stock_posts(symbol='NVDA')
# print(posts)

#fetch_mastodon_stock_posts(symbol='RBLX')

#fetch_reddit_symbol_top_praw(symbol=q)
# fetch_finnhub_world_news()
# print(pick_fundamental_source('NVDA'))

# print(get_stock_data("AAPL", "2025-11-01", "2025-11-20"))