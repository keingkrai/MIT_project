# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# import time
# import json
# # from tradingagents.agents.utils.agent_utils import get_indicators
# from tradingagents.dataflows.core_indicator import get_indicators
# from tradingagents.dataflows.core_stock_price import get_stock_data
# from tradingagents.dataflows.config import get_config


# def create_market_analyst(llm):

#     def market_analyst_node(state):
#         current_date = state["trade_date"]
#         ticker = state["company_of_interest"]
#         company_name = state["company_of_interest"]

#         tools = [
#             get_stock_data,
#             get_indicators,
#         ]

#         system_message = (
#             """You are a trading assistant tasked with analyzing financial markets. Your role is to select the **most relevant indicators** for a given market condition or trading strategy from the following list. The goal is to choose up to **8 indicators** that provide complementary insights without redundancy. Categories and each category's indicators are:

# Moving Averages:
# - close_50_sma: 50 SMA: A medium-term trend indicator. Usage: Identify trend direction and serve as dynamic support/resistance. Tips: It lags price; combine with faster indicators for timely signals.
# - close_200_sma: 200 SMA: A long-term trend benchmark. Usage: Confirm overall market trend and identify golden/death cross setups. Tips: It reacts slowly; best for strategic trend confirmation rather than frequent trading entries.
# - close_10_ema: 10 EMA: A responsive short-term average. Usage: Capture quick shifts in momentum and potential entry points. Tips: Prone to noise in choppy markets; use alongside longer averages for filtering false signals.

# MACD Related:
# - macd: MACD: Computes momentum via differences of EMAs. Usage: Look for crossovers and divergence as signals of trend changes. Tips: Confirm with other indicators in low-volatility or sideways markets.
# - macds: MACD Signal: An EMA smoothing of the MACD line. Usage: Use crossovers with the MACD line to trigger trades. Tips: Should be part of a broader strategy to avoid false positives.
# - macdh: MACD Histogram: Shows the gap between the MACD line and its signal. Usage: Visualize momentum strength and spot divergence early. Tips: Can be volatile; complement with additional filters in fast-moving markets.

# Momentum Indicators:
# - rsi: RSI: Measures momentum to flag overbought/oversold conditions. Usage: Apply 70/30 thresholds and watch for divergence to signal reversals. Tips: In strong trends, RSI may remain extreme; always cross-check with trend analysis.

# Volatility Indicators:
# - boll: Bollinger Middle: A 20 SMA serving as the basis for Bollinger Bands. Usage: Acts as a dynamic benchmark for price movement. Tips: Combine with the upper and lower bands to effectively spot breakouts or reversals.
# - boll_ub: Bollinger Upper Band: Typically 2 standard deviations above the middle line. Usage: Signals potential overbought conditions and breakout zones. Tips: Confirm signals with other tools; prices may ride the band in strong trends.
# - boll_lb: Bollinger Lower Band: Typically 2 standard deviations below the middle line. Usage: Indicates potential oversold conditions. Tips: Use additional analysis to avoid false reversal signals.
# - atr: ATR: Averages true range to measure volatility. Usage: Set stop-loss levels and adjust position sizes based on current market volatility. Tips: It's a reactive measure, so use it as part of a broader risk management strategy.

# Volume-Based Indicators:
# - vwma: VWMA: A moving average weighted by volume. Usage: Confirm trends by integrating price action with volume data. Tips: Watch for skewed results from volume spikes; use in combination with other volume analyses.

# - Select indicators that provide diverse and complementary information. Avoid redundancy (e.g., do not select both rsi and stochrsi). Also briefly explain why they are suitable for the given market context. When you tool call, please use the exact name of the indicators provided above as they are defined parameters, otherwise your call will fail. Please make sure to call get_stock_data first to retrieve the CSV that is needed to generate indicators. Then use get_indicators with the specific indicator names. Write a very detailed and nuanced report of the trends you observe. Do not simply state the trends are mixed, provide detailed and finegrained analysis and insights that may help traders make decisions."""
#             + """ Make sure to append a Markdown table at the end of the report to organize key points in the report, organized and easy to read."""
#         )

#         prompt = ChatPromptTemplate.from_messages(
#             [
#                 (
#                     "system",
#                     "You are a helpful AI assistant, collaborating with other assistants."
#                     " Use the provided tools to progress towards answering the question."
#                     " If you are unable to fully answer, that's OK; another assistant with different tools"
#                     " will help where you left off. Execute what you can to make progress."
#                     " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
#                     " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
#                     " You have access to the following tools: {tool_names}.\n{system_message}"
#                     "For your reference, the current date is {current_date}. The company we want to look at is {ticker}",
#                 ),
#                 MessagesPlaceholder(variable_name="messages"),
#             ]
#         )

#         prompt = prompt.partial(system_message=system_message)
#         prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
#         prompt = prompt.partial(current_date=current_date)
#         prompt = prompt.partial(ticker=ticker)

#         chain = prompt | llm.bind_tools(tools)

#         result = chain.invoke(state["messages"])

#         report = ""

#         if len(result.tool_calls) == 0:
#             report = result.content
       
#         return {
#             "messages": [result],
#             "market_report": report,
#         }

#     return market_analyst_node

import re
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import json
from tradingagents.dataflows.core_indicator import get_indicators
from tradingagents.dataflows.core_stock_price import get_stock_data


def create_market_analyst(llm):

    def market_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        tools = [
            get_stock_data,
            get_indicators,
        ]

        # -------------------------------------------------------------
        # SYSTEM MESSAGE (JSON FORMAT ANALYST)
        # -------------------------------------------------------------
        system_message = """
You are an AI Trading Analysis Agent.  
Your task is to analyze the market conditions, indicators, price action, and sentiment of a given stock.  
You MUST return the final output strictly in valid JSON format with no additional text, explanations, or commentary.

DATA REQUIREMENTS:
- When calling get_stock_data: fetch exactly 1 year of historical price data from the reference date.
- When calling get_indicators: compute indicators using the most recent 1 month (30 days) of price data only.
- You must ALWAYS call get_stock_data first, then call get_indicators using the indicator names selected.
- When calling get_indicators, use the EXACT indicator names below (case-sensitive). If any indicator cannot be computed, still include it in "selected_indicators" but set its signal and implication to a short inferred statement and mark confidence via overall confidence_score.

MANDATORY INDICATOR LIST (USE THESE EXACT NAMES IN get_indicators):
[
    "close_50_sma",
    "close_200_sma",
    "close_10_ema",
    "macd",
    "macds",
    "macdh",
    "rsi",
    "boll",
    "boll_ub",
    "boll_lb",
    "atr",
    "vwma"
]

RULES:
1. Output must be a valid JSON object.
2. Use EXACTLY the structure shown below.
3. Do not add or remove any fields.
4. Keep analysis concise, realistic, and trading-focused.
5. If any data is missing, infer reasonable values.

JSON FORMAT STRUCTURE:

{
    "ticker": "AAPL",
    "date": "2025-12-04",

    "selected_indicators": [
        "close_50_sma",
        "close_200_sma",
        "close_10_ema",
        "macd",
        "macds",
        "macdh",
        "rsi",
        "boll",
        "boll_ub",
        "boll_lb",
        "atr",
        "vwma"
    ],


    "market_overview": {
        "trend_direction": "Bullish | Bearish | Sideways",
        "momentum_state": "Strong Momentum | Weak Momentum | Diverging | Reversing",
        "volatility_level": "Low | Moderate | High",
        "volume_condition": "Rising Volume | Falling Volume | Neutral"
    },

    "indicator_analysis": [
        {
            "indicator": "close_50_sma",
            "signal": "Price trading above 50 SMA indicates medium-term bullish trend.",
            "implication": "Suggests buyers remain in control."
        }
    ],

    "price_action_summary": {
        "recent_high_low": "Price is near recent 20-day high.",
        "support_levels": ["150", "145"],
        "resistance_levels": ["165", "170"],
        "short_term_behavior": "Price consolidating above 50 SMA with decreasing volatility."
    },

    "market_sentiment": {
        "sentiment_score": 72,
        "sentiment_label": "Bullish"
    },

    "key_risks": [
        "Momentum overstretched near resistance.",
        "Volatility spike may invalidate current trends.",
        "MACD divergence forming on the last 3 sessions."
    ],

    "short_term_outlook": "Bullish continuation likely if price stays above 50 SMA and MACD remains positive.",
    "confidence_score": 0.85
}

Return ONLY the JSON object.
"""

        # -------------------------------------------------------------
        # PROMPT TEMPLATE
        # -------------------------------------------------------------
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant, collaborating with other assistants. "
                    "Use the provided tools to progress towards answering the question. "
                    "If you cannot finish, another assistant will continue. "
                    "If you ever reach the FINAL TRANSACTION PROPOSAL (BUY/HOLD/SELL), "
                    "prefix with: FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**. "
                    "You have access to the following tools: {tool_names}. \n\n"
                    "{system_message}\n\n"
                    "For your reference, the current date is {current_date}. "
                    "The company we want to look at is {ticker}."
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        # Insert dynamic runtime variables
        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)

        # Build the chain
        chain = prompt | llm.bind_tools(tools)

        # LLM output
        result = chain.invoke(state["messages"])

        report = ""

        # If no tool call → final JSON is in result.content
        if len(result.tool_calls) == 0:
            report = result.content

            raw = report

            # 1) Clean markdown fences
            clean = re.sub(r"```[\w]*", "", raw).replace("```", "").strip()

            # 2) Try parse JSON
            try:
                parsed = json.loads(clean)
                report = parsed
            except:
                report = clean

            # 3) If parsed successfully (Python dict), convert back to pretty JSON
            if isinstance(report, dict):
                report = json.dumps(report, indent=4)

        return {
            "messages": [result],
            "market_report": report,
        }

    return market_analyst_node

