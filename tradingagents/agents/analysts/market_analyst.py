import json
import re
from typing import List, Literal
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser
from tradingagents.dataflows.core_indicator import get_indicators
from tradingagents.dataflows.core_stock_price import get_stock_data


# ===================== PYDANTIC MODELS ======================
class MarketOverview(BaseModel):
    trend_direction: Literal["Bullish", "Bearish", "Sideways"] = Field(description="Primary trend direction")
    momentum_state: Literal["Strong", "Weak", "Diverging", "Neutral"] = Field(description="Momentum state")
    volatility_level: Literal["Low", "Moderate", "High"] = Field(description="Volatility based on ATR/Bollinger")
    volume_condition: Literal["Rising", "Falling", "Neutral"] = Field(description="Volume trend analysis")


class IndicatorAnalysis(BaseModel):
    indicator: str = Field(description="Short code of the indicator (e.g. close_50_sma).")
    indicator_full_name: str = Field(description="Full name of the indicator.")
    signal: str = Field(description="Detailed signal description.")
    implication: str = Field(description="Trading implication of the signal.")


class PriceActionSummary(BaseModel):
    recent_high_low: str = Field(description="Price position relative to recent highs/lows.")
    support_levels: List[str] = Field(description="List of immediate support price levels.")
    resistance_levels: List[str] = Field(description="List of immediate resistance price levels.")
    short_term_behavior: str = Field(description="Description of short-term price action.")


class MarketSentiment(BaseModel):
    sentiment_label: str = Field(description="Sentiment label: Bullish/Bearish.")


class MarketReport(BaseModel):
    ticker: str = Field(description="The ticker symbol of the company.")
    date: str = Field(description="The current analysis date (YYYY-MM-DD).")
    selected_indicators: List[str] = Field(description="List of indicators used.")
    market_overview: MarketOverview
    indicator_analysis: List[IndicatorAnalysis]
    price_action_summary: PriceActionSummary
    market_sentiment: MarketSentiment
    key_risks: List[str] = Field(description="List of key technical risks.")
    short_term_outlook: str = Field(description="Concise outlook statement.")

# ===================== AGENT FACTORY ======================
def create_market_analyst(llm):
    parser = JsonOutputParser(pydantic_object=MarketReport)

    def market_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        
        # Calculate date range
        try:
            curr_date_obj = datetime.strptime(current_date, "%Y-%m-%d")
            start_date = (curr_date_obj - timedelta(days=365)).strftime("%Y-%m-%d")
        except Exception:
            start_date = "2024-01-01"

        tools = [get_stock_data, get_indicators]

        # ===================== SYSTEM MESSAGE ======================
        system_message = f"""
You are an AI Trading Analysis Agent.

Rules:
1) You MUST call `get_stock_data` FIRST using exactly 1 year of historical data (Start: {start_date}, End: {current_date}).
2) You MUST call `get_indicators` SECOND using only the most recent 30 days of the fetched price data.
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

OUTPUT FORMAT:
{parser.get_format_instructions()}

Return ONLY the JSON object, no markdown code blocks.
"""

        # ===================== PROMPT ======================
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are a helpful AI assistant, collaborating with other assistants. "
                "Use the provided tools to progress towards answering the question. "
                "You have access to the following tools: {tool_names}. \n\n"
                "{system_message}\n\n"
                "For your reference, the current date is {current_date}. "
                "The company we want to look at is {ticker}."
            ),
            MessagesPlaceholder(variable_name="messages"),
        ])

        prompt = prompt.partial(
            system_message=system_message,
            tool_names=", ".join([tool.name for tool in tools]),
            current_date=current_date,
            ticker=ticker
        )

        # ===================== CHAIN ======================
        chain = prompt | llm.bind_tools(tools)

        # Execute
        result = chain.invoke(state["messages"])
        
        # print("Market Analysis Result:", result)
        
        # ========== PARSE WITH ROBUST ERROR HANDLING ==========
        report_dict = None
        
        if not result.tool_calls:
            raw_content = result.content
            
            # Handle list format (e.g., [{'type': 'text', 'text': '...'}])
            if isinstance(raw_content, list):
                for item in raw_content:
                    if isinstance(item, dict) and item.get('type') == 'text':
                        raw_content = item.get('text', '')
                        break
                else:
                    raw_content = " ".join([str(item) for item in raw_content])
            
            if raw_content is None:
                raw_content = ""
            
            try:
                # Method 1: Use Parser (handles string cleaning internally)
                report_dict = parser.parse(str(raw_content))
                
            except Exception as e1:
                print(f"⚠️ Parser failed: {e1}")
                
                # Method 2: Clean markdown and extract JSON
                try:
                    clean = re.sub(r"```[\w]*\n?", "", str(raw_content)).strip()
                    match = re.search(r"\{[\s\S]*\}", clean)
                    
                    if match:
                        json_str = match.group(0)
                        report_dict = json.loads(json_str)
                        # Validate with Pydantic
                        report_dict = MarketReport.model_validate(report_dict).model_dump()
                    else:
                        print("⚠️ No JSON object found in response")
                        report_dict = {"error": "No JSON found", "raw": str(raw_content)[:200]}
                        
                except Exception as e2:
                    print(f"⚠️ Fallback parsing failed: {e2}")
                    report_dict = {"error": "Parsing failed", "raw": str(raw_content)[:200]}
        
        # If still None (tool_calls present), create empty structure
        if report_dict is None:
            report_dict = {"status": "waiting_for_tool_response"}

        # Convert dict to JSON string
        report_json = json.dumps(report_dict, indent=4, ensure_ascii=False)

        print("Market Report JSON:", report_json)

        return {
            "messages": [result],
            "market_report": report_json,  # Return as JSON string
        }

    return market_analyst_node