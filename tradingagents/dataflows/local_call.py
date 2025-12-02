from typing import Annotated
from .local import alphavantage_get_company_news, get_world_news_yf, fetch_reddit_world_news, fetch_reddit_symbol_top_praw, fetch_mastodon_stock_posts, fetch_bsky_stock_posts, pick_fundamental_source, finnhub_get_company_news, reddit_get_company_news, yfinance_get_company_news, fetch_finnhub_world_news, fetch_and_choose
import os, requests
from rich.console import Console

console = Console()

def sent_to_telegram(message: str):
    """Send a message to Telegram if configured."""
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown",
        }
        try:
            response = requests.post(url, data=payload, timeout=10)
            response.raise_for_status()
            console.print("[green]Report sent to Telegram successfully![/green]")
        except requests.RequestException as e:
            console.print(f"[red]Failed to send report to Telegram: {e}[/red]")
    else:
        console.print("[yellow]Telegram not configured. Skipping sending report.[/yellow]")
 
#fundamental data
def get_fundamentals_local(ticker, curr_date):
    """
    มีการรับ parameter ตามรูปบบที่ต้นฉบับใช้เพื่อความรวดเร็วและลดการแก้ไขมากที่สุด
    แต่ในฟังก์ชันนี้จะใช้แค่ ticker เพื่อดึงข้อมูล
    """
        
    res = pick_fundamental_source(ticker)
    
    # print(f'\n\n\n [get_fundamentals_local] Chosen fundamental data source result:\n{res}\n\n\n')
    
    # read text and send to telegram
    with open("all_report_message.txt", "r", encoding="utf-8") as f:
        report_messages = f.read()
        sent_to_telegram(report_messages)
        
    return res

#company news data
def get_finnhub_company_news(
    query: Annotated[str, "Search query or ticker symbol"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
):
    res = finnhub_get_company_news(query)
    # print(f'\n\n\n [get_finnhub_company_news] Finnhub company news result:\n{res}\n\n\n')
    return res

def get_reddit_company_news(
    query: Annotated[str, "Search query or ticker symbol"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    
    res = reddit_get_company_news(query)
    # print(f'\n\n\n [get_reddit_company_news] Reddit company news result:\n{res}\n\n\n')
    return res

def get_yfinance_company_news(
    query: Annotated[str, "Query to search with"],
    curr_date: Annotated[str, "Curr date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "how many days to look back"],
) -> str:

    res = yfinance_get_company_news(query)
    # print(f'\n\n\n [get_yfinance_company_news] YFinance company news result:\n{res}\n\n\n')
    return res

def get_alphavantage_company_news(
    query: Annotated[str, "Query to search with"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:

    res = alphavantage_get_company_news(query)
    # print(f'\n\n\n [get_alphavantage_company_news] AlphaVantage company news result:\n{res}\n\n\n')
    return res


#global news data
def get_yfinance_world_news(
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "Number of days to look back"] = 7,
    limit: Annotated[int, "Maximum number of articles to return"] = 5,
) -> str:

    res = get_world_news_yf()
    
    count = len(res)
    report_message =  f"Yfinance global news have : {count} posts."
                     
    # write text file
    with open("all_report_message.txt", "a", encoding='utf-8') as file:
        file.write(report_message + "\n")
    # print(f'\n\n\n [get_reddit_world_news] Reddit world news result:\n{res}\n\n\n')
    return res

def get_reddit_world_news(
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "Number of days to look back"] = 7,
    limit: Annotated[int, "Maximum number of articles to return"] = 5,
) -> str:

    res = fetch_reddit_world_news()
    
    count = len(res)
    report_message = f"🌏 Global News: \n" \
                     f"Reddit global news have : {count} posts."
                     
    # write text file
    with open("all_report_message.txt", "a", encoding='utf-8') as file:
        file.write("\n" + report_message + "\n")
        
    return res

def get_finnhub_world_news(
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "Number of days to look back"] = 7,
    limit: Annotated[int, "Maximum number of articles to return"] = 5,
) -> str:

    res = fetch_finnhub_world_news()
    # print(f'\n\n\n [get_finnhub_world_news] Finnhub world news result:\n{res}\n\n\n')
    
    count = len(res)
    report_message = f"Finnhub global news have : {count} posts."
                     
    # write text file
    with open("all_report_message.txt", "a", encoding='utf-8') as file:
        file.write(report_message + "\n\n")
    return res


#indicator data
def get_indicator(
    symbol: Annotated[str, "ticker symbol of the company"],
    indicator: Annotated[str, "technical indicator to get the analysis and report of"],
    curr_date: Annotated[
        str, "The current trading date you are trading on, YYYY-mm-dd"
    ],
    look_back_days: Annotated[int, "how many days to look back"],
) -> str:
    
    res = fetch_and_choose(symbol)
    print(f'\n\n\n [get_indicator] Indicator result:\n\n\n\n')
    return res


#social media news
def get_bluesky_news(
    ticker: Annotated[str, "ticker symbol of the company"]
):
    res = fetch_bsky_stock_posts(ticker)
    print(f'\n\n\n [get_bluesky_news] Bluesky news result:\n\n\n\n')

    count = len(res)
    report_message = f"🌐 Social Media News: \n" \
                     f"Bluesky news fetched for {ticker}: {count} posts found."

    # write text file
    with open("all_report_message.txt", "a", encoding='utf-8') as file:
        file.write("\n" + report_message + "\n")

    return res

def get_mastodon_news(
    ticker: Annotated[str, "ticker symbol of the company"]
):
    res = fetch_mastodon_stock_posts(ticker)
    print(f'\n\n\n [get_mastodon_news] Mastodon news result:\n\n\n\n')

    count = len(res)
    report_message = f"Mastodon news fetched for {ticker}: {count} posts found."

    # write text file
    with open("all_report_message.txt", "a") as file:
        file.write(report_message + "\n")

    return res

def get_subreddit_news(
    symbol: Annotated[str, "ticker symbol of the company"]
):
    res = fetch_reddit_symbol_top_praw(symbol)
    print(f'\n\n\n [get_subreddit_news] Subreddit news result:\n\n\n\n')

    count = len(res)
    report_message = f"Subreddit news fetched for {symbol}: {count} posts found."

    # write text file
    with open("all_report_message.txt", "a") as file:
        file.write(report_message + "\n\n")

    return res