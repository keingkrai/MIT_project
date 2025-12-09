from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List, Dict
from datetime import datetime, timedelta
import json
import re

# ตรวจสอบ path ให้ตรง
from tradingagents.dataflows.core_indicator import get_indicators
from tradingagents.dataflows.core_stock_price import get_stock_data

def create_market_analyst(llm):

    # -------------------------------------------------------------
    # 1. Define Pydantic Models (โครงสร้าง JSON)
    # -------------------------------------------------------------
    class MarketOverview(BaseModel):
        trend_direction: str = Field(description="Primary trend direction: Bullish, Bearish, or Sideways.")
        momentum_state: str = Field(description="Momentum description e.g., Strong, Weak, Diverging.")
        volatility_level: str = Field(description="Volatility level: Low, Moderate, High.")
        volume_condition: str = Field(description="Volume analysis: Rising, Falling, Neutral.")

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
        sentiment_score: int = Field(description="Score from 0-100.")
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
        confidence_score: float = Field(description="Confidence score between 0.0 and 1.0.")

    # สร้าง Parser
    parser = JsonOutputParser(pydantic_object=MarketReport)

    def market_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        
        # คำนวณวันย้อนหลัง
        try:
            curr_date_obj = datetime.strptime(current_date, "%Y-%m-%d")
            start_date = (curr_date_obj - timedelta(days=365)).strftime("%Y-%m-%d")
        except Exception:
            start_date = "2024-01-01"

        tools = [get_stock_data, get_indicators]

        # -------------------------------------------------------------
        # 2. System Message (ใช้ format_instructions จาก Parser)
        # -------------------------------------------------------------
        system_message = f"""
You are an AI Trading Analysis Agent.

Rules:
1) You MUST call `get_stock_data` FIRST using exactly 1 year of historical data (Start: {start_date}, End: {current_date}).
2) You MUST call `get_indicators` SECOND using only the most recent 30 days.
3) Use ONLY the following indicator codes for the tool call:
   [close_50_sma, close_200_sma, close_10_ema, macd, macds, macdh, rsi, boll, boll_ub, boll_lb, atr, vwma]

4) **OUTPUT FORMAT:**
   You must return a valid JSON object matching the schema below.
   Do not wrap the output in markdown blocks.
   
   {parser.get_format_instructions()}
"""

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant... \n{system_message}\n"
                    "For reference: Date={current_date}, Ticker={ticker}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(
            system_message=system_message,
            tool_names=", ".join([tool.name for tool in tools]),
            current_date=current_date,
            ticker=ticker
        )

        chain = prompt | llm.bind_tools(tools)

        # Call Chain
        result = chain.invoke({"messages": state["messages"]})

        report_content = ""
        
        print("market analysis: ", result)
        
        # -------------------------------------------------------------
        # 3. Robust Parsing Logic (ใช้ Parser ของ LangChain)
        # -------------------------------------------------------------
        if not result.tool_calls:
            raw_content = result.content
            
            # Clean list to string if needed
            if isinstance(raw_content, list):
                raw_content = " ".join([str(item) for item in raw_content])
            if raw_content is None: raw_content = ""

            try:
                # 1. ลองใช้ Parser มาตรฐานก่อน
                parsed_json = parser.parse(raw_content)
                report_content = json.dumps(parsed_json, indent=4, ensure_ascii=False)
                
            except Exception:
                # 2. ถ้าพัง ให้ใช้ Regex ช่วย (Fallback)
                try:
                    match = re.search(r"\{[\s\S]*\}", raw_content)
                    if match:
                        json_str = match.group(0)
                        parsed_json = json.loads(json_str)
                        report_content = json.dumps(parsed_json, indent=4, ensure_ascii=False)
                    else:
                        print("⚠️ Market Analyst: No JSON found via Regex.")
                        report_content = json.dumps({"error": "No JSON found", "raw": raw_content[:200]})
                except Exception as e:
                    print(f"⚠️ Market Analyst: Parsing Error ({e}). Saving raw content.")
                    report_content = raw_content

        return {
            "messages": [result],
            "market_report": report_content,
        }

    return market_analyst_node