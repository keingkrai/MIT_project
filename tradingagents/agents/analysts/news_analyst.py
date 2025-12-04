from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from datetime import datetime, timedelta
import time
import json
import re

# ตรวจสอบ path ให้ตรง
from tradingagents.agents.utils.agent_utils import get_news, get_global_news
from tradingagents.dataflows.config import get_config

def extract_first_json(text):
    """
    Extract the first valid JSON object from text by counting braces.
    """
    text = text.strip()
    start_index = text.find('{')
    if start_index == -1:
        return None
    
    count = 0
    for i, char in enumerate(text[start_index:], start=start_index):
        if char == '{':
            count += 1
        elif char == '}':
            count -= 1
        
        if count == 0:
            return text[start_index : i + 1]
    
    return None

def create_news_analyst(llm):
    def news_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        # --- 1. คำนวณวันย้อนหลัง 7 วัน ---
        try:
            curr_date_obj = datetime.strptime(current_date, "%Y-%m-%d")
            start_date = (curr_date_obj - timedelta(days=7)).strftime("%Y-%m-%d")
        except Exception:
            start_date = "2024-01-01"

        tools = [get_news, get_global_news]

        # --- 2. Detailed JSON System Prompt ---
        system_message = (
            f"""Act as a Senior Market News Analyst.

    **CRITICAL INSTRUCTION:**
    - You **DO NOT** have access to real-time news in your internal memory.
    - You **MUST CALL** the `get_global_news` and `get_news` tools IMMEDIATELY to fetch data.
    - **DO NOT** hallucinate or invent news. If you do not call the tools, you cannot complete this task.
    - **Output JSON ONLY.**

    **YOUR MANDATORY WORKFLOW:**
    1. **Step 1:** Invoke call `get_global_news(curr_date='{current_date}', look_back_days=7, limit=5)`.
    2. **Step 2:** Invoke call `get_news(query='{ticker}', start_date='{start_date}', end_date='{current_date}')`.
    3. **Step 3:** Wait for tool outputs.
    4. **Step 4:** Synthesize the data into the required JSON format.

    **STRICT FORMATTING RULES:**
    - **NO ABBREVIATIONS:** Use full names (e.g., Federal Reserve, Year over Year).
    - **Output JSON ONLY DON'T HAVE ANYTHING ELSE.**
    
    **IMPORTENT**
    - JSON format below only.
    - Check anythink it in rules before sent.

    **JSON STRUCTURE:**
    {{
        "executive_summary": "String: A detailed paragraph summarizing the single most important story driving the stock right now.",
        "market_sentiment_score": "Number: 0 (Negative) to 100 (Positive)",
        "market_sentiment_verdict": "String: Bullish / Bearish / Neutral",
        "global_macro_context": {{
            "economic_policy_analysis": "String: Analysis of Central Bank actions and Interest Rates.",
            "geopolitical_impact": "String: Analysis of wars, trade bans, or elections affecting the sector."
        }},
        "company_specific_developments": [
            {{
                "headline": "String: Full headline",
                "source": "String: News Source",
                "date": "String: YYYY-MM-DD",
                "sentiment_impact": "String: Positive / Negative",
                "detailed_implication": "String: A full sentence explaining WHY this matters for the stock price."
            }}
        ],
        "key_risks_identified": [
            "String: Detailed risk factor 1",
            "String: Detailed risk factor 2"
        ]
    }}
    """
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant... \n{system_message}\n"
                    "For your reference, the current date is {current_date}. We are looking at the company {ticker}",
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
        
        result = None # ประกาศตัวแปรรอไว้ก่อน

        try:
            print("🚀 Invoking News Analyst Chain...")
            result = chain.invoke({"messages": state["messages"]})
            print("✅ Chain invocation succeeded")
            
        except Exception as e:
            print(f"❌ Chain invocation failed: {e}")
            # ถ้าพังตรงนี้ ต้อง return ค่าว่าง หรือ error message กลับไปเลย
            # ไม่งั้นโค้ดบรรทัดล่างจะพังตามไปด้วย
            return {
                "messages": state["messages"], # คืนค่าเดิม
                "news_report": f"Error during analysis: {e}"
            }

        report_content = ""
    
        
        # --- 3. JSON Parsing Logic ---
        if not result.tool_calls:
            raw_content = result.content
            
            # 1. แปลง List เป็น String (กันเหนียว)
            if isinstance(raw_content, list):
                raw_content = " ".join([str(item) for item in raw_content])
            if raw_content is None:
                raw_content = ""
                  
            print("this result :", raw_content)

            try:
                # 2. ใช้ Regex ค้นหา JSON Object {...} ที่แท้จริง
                # มองหาปีกกาเปิดตัวแรก { และปีกกาปิดตัวสุดท้าย }
                match = re.search(r"\{.*\}", raw_content, re.DOTALL)
                
                if match:
                    json_str = match.group(0) # ดึงเฉพาะส่วนที่เป็น JSON
                    parsed_json = json.loads(json_str)
                    report_content = json.dumps(parsed_json, indent=4, ensure_ascii=False)
                else:
                    # ถ้าหาไม่เจอจริงๆ ให้ Error ไป
                    raise ValueError("No JSON object found in response")
                
            except (json.JSONDecodeError, ValueError) as e:
                print(f"⚠️ News Analyst: JSON Parse Error ({e}). Saving raw content.")
                # ถ้าพังจริงๆ ก็เก็บค่าดิบไว้ ดีกว่าไม่ได้อะไรเลย
                report_content = str(raw_content)

        return {
            "messages": [result],
            "news_report": report_content,
        }

    return news_analyst_node