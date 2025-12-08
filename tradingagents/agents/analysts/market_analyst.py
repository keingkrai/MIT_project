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

Rules:
1) You MUST call get_stock_data FIRST using exactly 1 year of historical data from the given date.
2) You MUST call get_indicators SECOND using only the most recent 30 days of the fetched price data.
3) Use ONLY the following indicator names:

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

4) After receiving indicator results, return the final answer as a valid JSON object ONLY.
5) If any indicator fails, still include it with inferred signal + implication.
6) Keep analysis concise and trading-focused.

-------------------------------------------
FINAL JSON FORMAT (must match exactly):
-------------------------------------------

{
    "ticker": "",
    "date": "",

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
        "trend_direction": "",
        "momentum_state": "",
        "volatility_level": "",
        "volume_condition": ""
    },

    "indicator_analysis": [
        {
            "indicator": "close_50_sma",
            "indicator_full_name": "50-Day Simple Moving Average",
            "signal": "",
            "implication": ""
        }
    ],

    "price_action_summary": {
        "recent_high_low": "",
        "support_levels": [],
        "resistance_levels": [],
        "short_term_behavior": ""
    },

    "market_sentiment": {
        "sentiment_score": 0,
        "sentiment_label": ""
    },

    "key_risks": [],
    "short_term_outlook": "",
    "confidence_score": 0.0
}

Return ONLY the JSON.
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

        import re
        import json
        import ast  # for literal_eval fallback

        print(result.content)

        report = None
        raw = result.content

        # 1) Clean obvious markdown fences first
        clean = re.sub(r"```[\w]*", "", raw if isinstance(raw, str) else str(raw)).replace("```", "").strip()

        parsed = None

        # 2) Try JSON parse
        try:
            parsed = json.loads(clean)
        except Exception:
            # 3) If JSON parsing fails, try to interpret Python literal (e.g. "[{'type':'text', 'text': '...'}]")
            try:
                parsed = ast.literal_eval(clean)
            except Exception:
                parsed = None

        # 4) If parsed is a list, try common heuristics to extract the single JSON object we want
        if isinstance(parsed, list):
            # Case A: list of dicts where each dict has 'text' (e.g. [{'type':'text','text':'...'}])
            if all(isinstance(item, dict) and "text" in item for item in parsed):
                # join all text parts and try parse again
                joined = "\n".join(item["text"] for item in parsed)
                joined = re.sub(r"```[\w]*", "", joined).replace("```", "").strip()
                try:
                    parsed = json.loads(joined)
                except Exception:
                    try:
                        parsed = ast.literal_eval(joined)
                    except Exception:
                        # leave parsed as-is (list of dicts)
                        parsed = parsed
            # Case B: list with single element which is the JSON dict we want
            elif len(parsed) == 1 and isinstance(parsed[0], dict):
                parsed = parsed[0]
            # Otherwise keep parsed as list (maybe it's legitimately a list of items)

        # 5) If parsed is a dict -> pretty JSON string
        if isinstance(parsed, dict):
            report = json.dumps(parsed, indent=4)
        # If parsed is a list -> if first element is dict, pick it (common), else dump the list
        elif isinstance(parsed, list):
            if len(parsed) > 0 and isinstance(parsed[0], dict):
                report = json.dumps(parsed[0], indent=4)
            else:
                try:
                    report = json.dumps(parsed, indent=4)
                except Exception:
                    report = str(parsed)
        # 6) If parsed is None, fallback to `clean` (string). If it's still a list-like string that wraps JSON, try a final json.loads
        else:
            # final attempt: maybe clean itself is a JSON list string like "[{...}]"
            try:
                final_try = json.loads(clean)
                if isinstance(final_try, list) and len(final_try) == 1 and isinstance(final_try[0], dict):
                    report = json.dumps(final_try[0], indent=4)
                else:
                    report = json.dumps(final_try, indent=4) if not isinstance(final_try, (str, int, float)) else str(final_try)
            except Exception:
                report = clean

        # Ensure report is a string for downstream usage
        if isinstance(report, (dict, list)):
            report = json.dumps(report, indent=4)

        return {
            "messages": [result],
            "market_report": report,
        }

    return market_analyst_node

