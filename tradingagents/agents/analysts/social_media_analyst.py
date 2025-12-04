from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from datetime import datetime, timedelta
import time
import json
import re

# ตรวจสอบ path ให้ตรง
from tradingagents.agents.utils.agent_utils import get_news, get_social
from tradingagents.dataflows.config import get_config

def create_social_media_analyst(llm):
    def social_media_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        # --- 1. คำนวณวันย้อนหลัง 7 วัน ---
        try:
            curr_date_obj = datetime.strptime(current_date, "%Y-%m-%d")
            start_date = (curr_date_obj - timedelta(days=7)).strftime("%Y-%m-%d")
        except Exception:
            start_date = "2024-01-01"

        tools = [get_social]

        # --- 2. Force-Tool JSON System Prompt ---
        system_message = (
            """Act as a Senior Social Media & Sentiment Analyst. Gauge the market pulse for **{ticker}** from **{start_date} to {current_date}** and output strictly in **JSON format**.

    **CRITICAL INSTRUCTION:**
    - You **DO NOT** have real-time sentiment data.
    - You **MUST CALL** `get_social` IMMEDIATELY.
    - **Do not** hallucinate sentiment. If you do not call the tools, you fail.
    - **Output JSON ONLY DON'T HAVE ANYTHING ELSE.**

    **YOUR WORKFLOW:**
    1. **Step 1:** Call `get_social` (start_date='{start_date}', end_date='{current_date}').
    2. **Step 2:** Analyze the results.
    3. **Step 3:** Output the final report as a JSON object.

    **STRICT FORMATTING RULES:**
    - **NO ABBREVIATIONS / SLANG:** You MUST use formal full terms.
      - Forbidden: FOMO, FUD, ATH, YTD, HODL, BTFD, OP.
      - Required: Fear Of Missing Out, Fear Uncertainty and Doubt, All Time High, Year To Date, Hold On for Dear Life, Buy The Dip, Original Poster.
    - **Output JSON ONLY DON'T HAVE ANYTHING ELSE.**

    **JSON STRUCTURE:**
    {{
        "sentiment_score": "Number: 0 (Extreme Fear) to 100 (Extreme Greed)",
        "sentiment_verdict": "String: Bearish / Neutral / Bullish / Euphoric / Panic",
        "social_volume_analysis": "String: Detailed assessment of discussion volume.",
        "dominant_narrative": "String: A full sentence explaining the main story driving retail investors right now.",
        "top_discussion_topics": [
            {{
                "topic": "String: The subject being discussed",
                "sentiment_impact": "String: Positive / Negative",
                "detailed_analysis": "String: Deep dive into why people are talking about this and how they feel."
            }}
        ],
        "retail_psychology_assessment": "String: Analysis of crowd psychology."
    }}
    """
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant... \n{system_message}\n"
                    "For your reference, the current date is {current_date}. The current company we want to analyze is {ticker}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        # Bind variables
        prompt = prompt.partial(
            system_message=system_message,
            tool_names=", ".join([tool.name for tool in tools]),
            current_date=current_date,
            ticker=ticker,
            start_date=start_date
        )

        chain = prompt | llm.bind_tools(tools)

        # Call Chain (Send as dict)
        result = chain.invoke({"messages": state["messages"]})

        report_content = ""
        
        # --- 3. JSON Parsing Logic ---
        if not result.tool_calls:
            raw_content = result.content
            
            # 1. แปลง List เป็น String (กันเหนียว)
            if isinstance(raw_content, list):
                raw_content = " ".join([str(item) for item in raw_content])
            if raw_content is None:
                raw_content = ""

            try:
                # 2. ใช้ Regex ค้นหาปีกกาเปิด-ปิด {...} เพื่อดึงเฉพาะ JSON
                # re.DOTALL ช่วยให้หาข้ามบรรทัดได้
                match = re.search(r"\{.*\}", raw_content, re.DOTALL)
                
                if match:
                    json_str = match.group(0)
                    parsed_json = json.loads(json_str)
                    report_content = json.dumps(parsed_json, indent=4, ensure_ascii=False)
                else:
                    print("⚠️ Social Media Analyst: No JSON object found via Regex.")
                    report_content = raw_content # ถ้าหาไม่เจอจริงๆ ก็ส่ง text ดิบไป
                
            except Exception as e:
                print(f"⚠️ Social Media Analyst: Parsing Error ({e}). Saving raw content.")
                report_content = raw_content

        return {
            "messages": [result],
            "sentiment_report": report_content,
        }

    return social_media_analyst_node