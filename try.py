from langchain_core.tools import tool
from typing import Annotated
from tradingagents.dataflows.interface import route_to_vendor

from dotenv import load_dotenv

from tradingagents.dataflows.alpha_vantage import (
    get_alpha_vantage_stock,
    get_indicator as get_alpha_vantage_indicator,
    get_fundamentals as get_alpha_vantage_fundamentals,
    get_balance_sheet as get_alpha_vantage_balance_sheet,
    get_cashflow as get_alpha_vantage_cashflow,
    get_income_statement as get_alpha_vantage_income_statement,
    get_insider_transactions as get_alpha_vantage_insider_transactions,
    get_news as get_alpha_vantage_news
)

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
from tradingagents.dataflows.local_call import get_bluesky_news
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
# q = 'RBLX'
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

import pandas as pd
# a = finnhub_get_company_news("AAPL")
# df = pd.DataFrame(a)
# print(df)
# print(df.columns)
# print(len(df))

# a = reddit_get_company_news("AAPL")
# df = pd.DataFrame(a)
# print((df))
# print(df.columns)
# print(len(df))

# a = yfinance_get_company_news("AAPL")
# df = pd.DataFrame(a)
# print(len(df))
# print(df.columns)
# print(len(df))

# from pandas import json_normalize

# content_df = json_normalize(df['content'])
# print(content_df)

# import json
# import pandas as pd
# a = get_alpha_vantage_news("AAPL", datetime(2024, 11, 26, tzinfo=timezone.utc), datetime(2025, 11, 26, tzinfo=timezone.utc))

# # 1) Convert JSON string to Python dict
# data = json.loads(a)

# # 2) Extract the list of news items
# news_list = data.get("feed", [])

# # 3) Convert into DataFrame (flatten nested fields automatically)
# df_news = pd.json_normalize(news_list)

# print(df_news)
# print(len(df_news))

# res = get_bluesky_news("AAPL")
# print(len(res))
# df = pd.DataFrame(res)
# print(df)
# print(df.columns)
# print(len(df))
# [get_reddit_world_news, get_yfinance_world_news, get_finnhub_world_news]


# a = pick_fundamental_source("A")
# print(a)
