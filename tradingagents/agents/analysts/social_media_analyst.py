from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List, Dict
from datetime import datetime, timedelta
import json
import re

# ตรวจสอบ path ให้ตรง
from tradingagents.agents.utils.agent_utils import get_news, get_social
from tradingagents.dataflows.config import get_config

def create_social_media_analyst(llm):

    # -------------------------------------------------------------
    # 1. Define Pydantic Models (โครงสร้าง JSON)
    # -------------------------------------------------------------
    class DiscussionTopic(BaseModel):
        topic: str = Field(description="The specific subject being discussed.")
        sentiment_impact: str = Field(description="Impact on sentiment (Positive, Negative, or Mixed).")
        detailed_analysis: str = Field(description="Deep dive into the community's feelings and arguments about this topic.")

    class SocialMediaReport(BaseModel):
        sentiment_score: int = Field(description="Score from 0 (Extreme Fear) to 100 (Extreme Greed). Default 50 if neutral.")
        sentiment_verdict: str = Field(description="Overall verdict: Bearish, Neutral, Bullish, Euphoric, or Panic.")
        social_volume_analysis: str = Field(description="Assessment of discussion volume (e.g., 'Spike in mentions due to news').")
        dominant_narrative: str = Field(description="The main story driving retail investor sentiment.")
        top_discussion_topics: List[DiscussionTopic] = Field(description="List of key topics trending in discussions.")
        retail_psychology_assessment: str = Field(description="Analysis of crowd psychology (e.g., FOMO, Capitulation).")

    # สร้าง Parser
    parser = JsonOutputParser(pydantic_object=SocialMediaReport)

    def social_media_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        # คำนวณวันย้อนหลัง 7 วัน
        try:
            curr_date_obj = datetime.strptime(current_date, "%Y-%m-%d")
            start_date = (curr_date_obj - timedelta(days=7)).strftime("%Y-%m-%d")
        except Exception:
            start_date = "2024-01-01"

        tools = [get_social, get_news]

        # -------------------------------------------------------------
        # 2. System Message (ใช้ format_instructions จาก Parser)
        # -------------------------------------------------------------
        system_message = f"""
Act as a Senior Social Media & Sentiment Analyst. Gauge the market pulse for **{ticker}** from **{start_date} to {current_date}**.

**YOUR WORKFLOW:**
1. Call `get_social` to gather public discussions.
2. Call `get_news` to cross-check sentiment against real events.
3. Synthesize the findings into the required JSON format.

**STRICT FORMATTING RULES:**
- **NO SLANG/ABBREVIATIONS:** Use formal full terms in the JSON output.
  - ❌ Forbidden: FOMO, FUD, ATH, HODL.
  - ✅ Required: Fear Of Missing Out, Fear Uncertainty and Doubt, All Time High, Hold On for Dear Life.
- **OUTPUT JSON ONLY:** Do not include markdown or conversational text.

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
        
        print(result)

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
                # 1. ใช้ Parser มาตรฐาน
                parsed_json = parser.parse(raw_content)
                report_content = json.dumps(parsed_json, indent=4, ensure_ascii=False)
                
            except Exception:
                # 2. Fallback: ใช้ Regex ถ้า Parser พัง
                try:
                    match = re.search(r"\{[\s\S]*\}", raw_content)
                    if match:
                        json_str = match.group(0)
                        parsed_json = json.loads(json_str)
                        report_content = json.dumps(parsed_json, indent=4, ensure_ascii=False)
                    else:
                        print("⚠️ Social Media Analyst: No JSON found via Regex.")
                        # Create minimal valid JSON to prevent crash
                        fallback = {
                            "sentiment_score": 50,
                            "sentiment_verdict": "Neutral (Error)",
                            "social_volume_analysis": "Data unavailable.",
                            "dominant_narrative": "Parsing failed.",
                            "top_discussion_topics": [],
                            "retail_psychology_assessment": "Unknown"
                        }
                        report_content = json.dumps(fallback, indent=4)
                except Exception as e:
                    print(f"⚠️ Social Media Analyst: Parsing Error ({e}). Saving raw content.")
                    report_content = raw_content

        return {
            "messages": [result],
            "sentiment_report": report_content,
        }

    return social_media_analyst_node