import json
import re
from typing import List, Literal
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser

from tradingagents.agents.utils.agent_utils import get_news, get_global_news


# ===================== PYDANTIC MODELS ======================
class GlobalMacroContext(BaseModel):
    macro_summary: str = Field(description="Concise analysis of Central Bank, Interest Rates, and Geopolitics combined. Max 5 sentences.")

class CompanyNewsItem(BaseModel):
    headline: str
    source: str
    date: str
    sentiment: Literal["Positive", "Negative", "Neutral"] = Field(description="Strict label")
    implication: str = Field(description="One sentence on price impact.")

class NewsReport(BaseModel):
    executive_summary: str = Field(description="The single most important driver. Max 50 words.")
    market_sentiment_verdict: Literal["Bullish", "Bearish", "Neutral"]
    global_macro_context: GlobalMacroContext
    top_news_developments: List[CompanyNewsItem] = Field(description="Select ONLY top 3-5 most impactful items.")
    key_risks: List[str] = Field(description="Max 3 bullet points.")


# ===================== AGENT FACTORY ======================
def create_news_analyst(llm):
    parser = JsonOutputParser(pydantic_object=NewsReport)

    def news_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        # Calculate 7 days lookback
        try:
            curr_date_obj = datetime.strptime(current_date, "%Y-%m-%d")
            start_date = (curr_date_obj - timedelta(days=7)).strftime("%Y-%m-%d")
        except Exception:
            start_date = "2024-01-01"

        tools = [get_news, get_global_news]

        # ===================== SYSTEM MESSAGE ======================
        system_message = f"""
You are a Senior Market News Analyst specializing in financial news and market impact assessment.

**CRITICAL INSTRUCTION:**
- You **MUST CALL** both tools IMMEDIATELY to gather comprehensive data.
- **DO NOT** hallucinate or invent news stories.
- Base all analysis on actual news retrieved from the tools.

**MANDATORY WORKFLOW:**
1. Call `get_global_news(curr_date='{current_date}', look_back_days=7)` to gather macro news.
2. Call `get_news(ticker='{ticker}', start_date='{start_date}', end_date='{current_date}')` to gather company-specific news.
3. Analyze both macro and company-specific factors.
4. Synthesize findings into the required JSON format.

**ANALYSIS GUIDELINES:**
- Focus on material news that could impact stock price
- Connect macro trends to company performance
- Assess both immediate and long-term implications
- Identify specific risks from news events

**SENTIMENT SCORE GUIDE:**
- 0-20: Very Negative / Crisis
- 21-40: Negative / Bearish
- 41-60: Neutral / Mixed
- 61-80: Positive / Bullish
- 81-100: Very Positive / Strong Bullish

**OUTPUT FORMAT:**
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
        
        print("News Analysis Result:", result)

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
                        report_dict = NewsReport.model_validate(report_dict).model_dump()
                    else:
                        print("⚠️ No JSON object found in response")
                        # Create minimal valid fallback
                        report_dict = {
                            "executive_summary": "Unable to retrieve news data for analysis.",
                            "market_sentiment_score": 50,
                            "market_sentiment_verdict": "Neutral (Data Unavailable)",
                            "global_macro_context": {
                                "economic_policy_analysis": "No data available.",
                                "geopolitical_impact": "No data available."
                            },
                            "company_specific_developments": [],
                            "key_risks_identified": ["Data retrieval error - unable to assess risks"]
                        }
                        
                except Exception as e2:
                    print(f"⚠️ Fallback parsing failed: {e2}")
                    report_dict = {
                        "executive_summary": "Error occurred during news analysis.",
                        "market_sentiment_score": 50,
                        "market_sentiment_verdict": "Error",
                        "global_macro_context": {
                            "economic_policy_analysis": "Error processing data.",
                            "geopolitical_impact": "Error processing data."
                        },
                        "company_specific_developments": [],
                        "key_risks_identified": ["Analysis error occurred"]
                    }
        
        # If still None (tool_calls present), create waiting structure
        if report_dict is None:
            report_dict = {"status": "waiting_for_tool_response"}

        # Convert dict to JSON string
        report_json = json.dumps(report_dict, indent=4, ensure_ascii=False)

        return {
            "messages": [result],
            "news_report": report_json,  # Return as JSON string
        }

    return news_analyst_node