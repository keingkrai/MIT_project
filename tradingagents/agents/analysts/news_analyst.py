from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List, Dict
from datetime import datetime, timedelta
import json
import re

# ตรวจสอบ path ให้ตรง
from tradingagents.agents.utils.agent_utils import get_news, get_global_news
from tradingagents.dataflows.config import get_config

def create_news_analyst(llm):

    # -------------------------------------------------------------
    # 1. Define Pydantic Models (โครงสร้าง JSON)
    # -------------------------------------------------------------
    class GlobalMacroContext(BaseModel):
        economic_policy_analysis: str = Field(description="Analysis of Central Bank actions and Interest Rates.")
        geopolitical_impact: str = Field(description="Analysis of wars, trade bans, or elections affecting the sector.")

    class CompanyNewsItem(BaseModel):
        headline: str = Field(description="Full headline of the news.")
        source: str = Field(description="News Source (e.g. Reuters, Bloomberg).")
        date: str = Field(description="Date of the news (YYYY-MM-DD).")
        sentiment_impact: str = Field(description="Impact on sentiment (Positive/Negative/Neutral).")
        detailed_implication: str = Field(description="A full sentence explaining WHY this matters for the stock price.")

    class NewsReport(BaseModel):
        executive_summary: str = Field(description="A detailed paragraph summarizing the single most important story driving the stock right now.")
        market_sentiment_score: int = Field(description="Score from 0 (Negative) to 100 (Positive).")
        market_sentiment_verdict: str = Field(description="Overall verdict: Bullish, Bearish, or Neutral.")
        global_macro_context: GlobalMacroContext
        company_specific_developments: List[CompanyNewsItem] = Field(description="List of key company-specific news items.")
        key_risks_identified: List[str] = Field(description="List of major risks identified from the news.")

    # สร้าง Parser
    parser = JsonOutputParser(pydantic_object=NewsReport)

    def news_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        # คำนวณวันย้อนหลัง
        try:
            curr_date_obj = datetime.strptime(current_date, "%Y-%m-%d")
            start_date = (curr_date_obj - timedelta(days=7)).strftime("%Y-%m-%d")
        except Exception:
            start_date = "2024-01-01"

        tools = [get_news, get_global_news]

        # -------------------------------------------------------------
        # 2. System Message (ใช้ format_instructions จาก Parser)
        # -------------------------------------------------------------
        system_message = f"""
        
            You are a Senior Market News Analyst.

            **CRITICAL INSTRUCTION:**
            - You **MUST CALL** the `get_global_news` and `get_news` tools IMMEDIATELY.
            - **DO NOT** hallucinate news.

            **MANDATORY WORKFLOW:**
            1. Call `get_global_news(curr_date='{current_date}', look_back_days=7)`.
            2. Call `get_news(ticker='{ticker}', start_date='{start_date}', end_date='{current_date}')`.
            3. Synthesize the findings into the required JSON format.

            **OUTPUT FORMAT:**
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
            ticker=ticker,
            start_date=start_date
        )

        chain = prompt | llm.bind_tools(tools)

        # Call Chain
        result = chain.invoke({"messages": state["messages"]})

        report_content = ""
        
        # -------------------------------------------------------------
        # 3. Robust Parsing Logic
        # -------------------------------------------------------------
        if not result.tool_calls:
            raw_content = result.content
            
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
                        print("⚠️ News Analyst: No JSON found via Regex.")
                        report_content = json.dumps({"error": "No JSON found", "raw": raw_content[:200]})
                except Exception as e:
                    print(f"⚠️ News Analyst: Parsing Error ({e}). Saving raw content.")
                    report_content = raw_content

        return {
            "messages": [result],
            "news_report": report_content,
        }

    return news_analyst_node