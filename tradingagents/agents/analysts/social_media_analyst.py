import json
import re
from typing import List, Literal
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser

from tradingagents.agents.utils.agent_utils import get_news, get_social


# ===================== PYDANTIC MODELS ======================
class DiscussionTopic(BaseModel):
    topic: str = Field(description="The subject.")
    sentiment: Literal["Positive", "Negative", "Mixed"] = Field(description="Feel in social")
    analysis_snippet: str = Field(description="Max 1 sentence summary of the crowd's opinion.")

class SocialMediaReport(BaseModel):
    sentiment_verdict: Literal["Bearish", "Neutral", "Bullish", "Euphoria", "Panic"]
    social_volume: str = Field(description="Brief assessment (e.g., 'Spike due to earnings').")
    dominant_narrative: str = Field(description="Main story driving retail. Max 2 sentences.")
    top_topics: List[DiscussionTopic] = Field(description="Select ONLY top 3-5 trending topics.")
    psychology: str = Field(description="Crowd psychology (e.g. FOMO, Capitulation).")

# ===================== AGENT FACTORY ======================
def create_social_media_analyst(llm):
    parser = JsonOutputParser(pydantic_object=SocialMediaReport)

    def social_media_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        # Calculate 7 days lookback
        try:
            curr_date_obj = datetime.strptime(current_date, "%Y-%m-%d")
            start_date = (curr_date_obj - timedelta(days=7)).strftime("%Y-%m-%d")
        except Exception:
            start_date = "2024-01-01"

        tools = [get_social]

        # ===================== SYSTEM MESSAGE ======================
        system_message = f"""
            Act as a Senior Social Media & Sentiment Analyst. Gauge the market pulse for **{ticker}** from **{start_date} to {current_date}**.

            **YOUR WORKFLOW:**
            1. Call `get_social` to gather public discussions (Reddit, Twitter, forums).
            2. Call `get_news` to cross-check sentiment against real events.
            3. Synthesize the findings into the required JSON format.

            **STRICT FORMATTING RULES:**
            - **NO SLANG/ABBREVIATIONS:** Use formal full terms in the JSON output.
            - ❌ Forbidden: FOMO, FUD, ATH, HODL, YOLO, etc.
            - ✅ Required: Fear Of Missing Out, Fear Uncertainty and Doubt, All Time High, Hold On for Dear Life, You Only Live Once.
            - **OUTPUT JSON ONLY:** Do not include markdown code blocks or conversational text.

            **SENTIMENT SCORE GUIDE:**
            - 0-20: Extreme Fear / Panic Selling
            - 21-40: Fear / Bearish
            - 41-60: Neutral / Mixed
            - 61-80: Greed / Bullish
            - 81-100: Extreme Greed / Euphoria

            {parser.get_format_instructions()}

            Return ONLY the JSON object.
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
                "The company we want to look at is {ticker}. "
                "Analysis period: {start_date} to {current_date}."
            ),
            MessagesPlaceholder(variable_name="messages"),
        ])

        prompt = prompt.partial(
            system_message=system_message,
            tool_names=", ".join([tool.name for tool in tools]),
            current_date=current_date,
            ticker=ticker,
            start_date=start_date
        )

        # ===================== CHAIN ======================
        chain = prompt | llm.bind_tools(tools)

        # Execute
        result = chain.invoke(state["messages"])
        
        print("Social Media Analysis Result:", result)

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
                        report_dict = SocialMediaReport.model_validate(report_dict).model_dump()
                    else:
                        print("⚠️ No JSON object found in response")
                        # Create minimal valid fallback
                        report_dict = {
                            "sentiment_score": 50,
                            "sentiment_verdict": "Neutral (Data Unavailable)",
                            "social_volume_analysis": "Unable to retrieve social media data.",
                            "dominant_narrative": "No clear narrative identified.",
                            "top_discussion_topics": [],
                            "retail_psychology_assessment": "Insufficient data for psychological assessment."
                        }
                        
                except Exception as e2:
                    print(f"⚠️ Fallback parsing failed: {e2}")
                    report_dict = {
                        "sentiment_score": 50,
                        "sentiment_verdict": "Error",
                        "social_volume_analysis": "Parsing error occurred.",
                        "dominant_narrative": "Error processing data.",
                        "top_discussion_topics": [],
                        "retail_psychology_assessment": "Error occurred during analysis."
                    }
        
        # If still None (tool_calls present), create waiting structure
        if report_dict is None:
            report_dict = {"status": "waiting_for_tool_response"}

        # Convert dict to JSON string
        report_json = json.dumps(report_dict, indent=4, ensure_ascii=False)

        return {
            "messages": [result],
            "sentiment_report": report_json,  # Return as JSON string
        }

    return social_media_analyst_node