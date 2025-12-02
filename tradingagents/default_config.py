import os

DEFAULT_CONFIG = {
    "project_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
    "results_dir": os.getenv("TRADINGAGENTS_RESULTS_DIR", "./results"),
    "data_dir": r"tradingagents\dataflows\data_cache",
    
    "data_cache_dir": os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
        "dataflows/data_cache",
    ),
    # LLM settings
    # "llm_provider": "openai",
    # "deep_think_llm": "o4-mini",
    # "quick_think_llm": "gpt-4o-mini",
    # "backend_url": "https://api.openai.com/v1",
    # LLM settings
    "llm_provider": "google",
    "deep_think_llm": "gemini-2.0-flash",
    "quick_think_llm": "gemini-2.0-flash-lite",
    # Debate and discussion settings
    "max_debate_rounds": 1,
    "max_risk_discuss_rounds": 1,
    "max_recur_limit": 100,
    # Data vendor configuration
    # Category-level configuration (default for all tools in category)
    "data_vendors": {
        "core_stock_apis": "core_stock_price",       # Options: yfinance, alpha_vantage, local
        "technical_indicators": "core_indicator",  # Options: yfinance, alpha_vantage, local
        "fundamental_data": "alpha_vantage", # Options: openai, alpha_vantage, local
        "news_data": "alpha_vantage",        # Options: openai, alpha_vantage, google, local
    },
    # Tool-level configuration (takes precedence over category-level)
    "tool_vendors": {
        # Example: "get_stock_data": "alpha_vantage",  # Override category default
        # Example: "get_news": "openai",
        # Override category default
        "get_stock_data": "local",
        "get_global_news": "local",
        "get_news": "local",
        "get_social": "local",
        "get_indicators": "local",
        "get_fundamentals": "local",
    },
}