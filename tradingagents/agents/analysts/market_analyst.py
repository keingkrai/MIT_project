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
        # 6) If parsed is None, fallback to clean (string). If it's still a list-like string that wraps JSON, try a final json.loads
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