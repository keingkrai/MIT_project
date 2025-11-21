from typing import Annotated
from .local import pick_fundamental_source, finnhub_get_company_news, reddit_get_company_news, yfinance_get_company_news, fetch_finnhub_world_news, fetch_and_choose

def get_fundamentals_local(ticker, curr_date):
    """
    มีการรับ parameter ตามรูปบบที่ต้นฉบับใช้เพื่อความรวดเร็วและลดการแก้ไขมากที่สุด
    แต่ในฟังก์ชันนี้จะใช้แค่ ticker เพื่อดึงข้อมูล
    """
        
    res = pick_fundamental_source(ticker)
    
    print(f'\n\n\n [get_fundamentals_local] Chosen fundamental data source result:\n{res}\n\n\n')
    return res

def get_finnhub_company_news(
    query: Annotated[str, "Search query or ticker symbol"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
):
    res = finnhub_get_company_news(query)
    print(f'\n\n\n [get_finnhub_company_news] Finnhub company news result:\n{res}\n\n\n')
    return res

def get_reddit_company_news(
    query: Annotated[str, "Search query or ticker symbol"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    
    res = reddit_get_company_news(query)
    print(f'\n\n\n [get_reddit_company_news] Reddit company news result:\n{res}\n\n\n')
    return res

def get_yfinance_company_news(
    query: Annotated[str, "Query to search with"],
    curr_date: Annotated[str, "Curr date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "how many days to look back"],
) -> str:

    res = yfinance_get_company_news(query)
    print(f'\n\n\n [get_yfinance_company_news] YFinance company news result:\n{res}\n\n\n')
    return res

def get_reddit_world_news(
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "Number of days to look back"] = 7,
    limit: Annotated[int, "Maximum number of articles to return"] = 5,
) -> str:

    res = fetch_finnhub_world_news()
    print(f'\n\n\n [get_reddit_world_news] Reddit world news result:\n{res}\n\n\n')
    return res

def get_indicator(
    symbol: Annotated[str, "ticker symbol of the company"],
    indicator: Annotated[str, "technical indicator to get the analysis and report of"],
    curr_date: Annotated[
        str, "The current trading date you are trading on, YYYY-mm-dd"
    ],
    look_back_days: Annotated[int, "how many days to look back"],
) -> str:
    
    res = fetch_and_choose(symbol)
    print(f'\n\n\n [get_indicator] Indicator result:\n{res}\n\n\n')
    return res