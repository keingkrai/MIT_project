from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from datetime import datetime, timedelta
import time
import json
import re

from tradingagents.dataflows.core_indicator import get_indicators
from tradingagents.dataflows.core_stock_price import get_stock_data
from tradingagents.dataflows.config import get_config

def create_market_analyst(llm):

    def market_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        
        try:
            curr_date_obj = datetime.strptime(current_date, "%Y-%m-%d")
            start_date = (curr_date_obj - timedelta(days=365)).strftime("%Y-%m-%d")
        except Exception:
            start_date = "2024-01-01"

        tools = [get_stock_data, get_indicators]

        system_message = (
            """Act as a Senior Technical Market Strategist. Conduct a deep-dive technical analysis of {ticker} and output the result strictly in **JSON format**.

    **DATA PARAMETERS:**
    - Start Date: {start_date}
    - End Date: {current_date}

    **INSTRUCTIONS:**
    1. Call `get_stock_data` first.
    2. Call `get_indicators`.
    3. **OUTPUT FORMAT:** Return a valid JSON object. No markdown formatting.
    
    **STRICT FORMATTING RULES:**
    - **NO ABBREVIATIONS:** Use full names in JSON Keys and Values.
    - **DETAIL:** Provide full sentences explaining the significance of the data.
    - **Output JSON ONLY DON'T HAVE ANYTHING ELSE.**

    **JSON STRUCTURE:**
    {{
        "primary_trend_assessment": {{
            "direction": "String: Bullish / Bearish / Sideways",
            "strength_description": "String: Detailed explanation."
        }},
        "critical_price_levels": {{
            "immediate_support_level": "String",
            "immediate_resistance_level": "String"
        }},
        "technical_signals_analysis": [ "String" ],
        "specific_indicators_analysis": {{
            "moving_averages_status": "String",
            "relative_strength_index_assessment": "String",
            "moving_average_convergence_divergence_status": "String",
            "bollinger_bands_analysis": "String",
            "average_true_range_volatility": "String",
            "volume_weighted_moving_average_status": "String"
        }}
    }}
    """
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant... \n{system_message}\n"
                    "For your reference, the current date is {current_date}. The company we want to look at is {ticker}",
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

        result = chain.invoke({"messages": state["messages"]})

        report_content = ""
        
        # --- 3. Robust JSON Parsing Logic (Updated) ---
        if not result.tool_calls:
            raw_content = result.content
            
            # แปลง List เป็น String
            if isinstance(raw_content, list):
                raw_content = " ".join([str(item) for item in raw_content])
            if raw_content is None:
                raw_content = ""
            
            # 🚨 เพิ่มบรรทัดนี้เพื่อดูว่า AI ตอบอะไรกลับมา
            print(f"\n🔍 DEBUG RAW CONTENT FROM MARKET ANALYST:\n{raw_content}\n{'='*30}")

            try:
                # ใช้ Regex ที่ยืดหยุ่นขึ้น (หาปีกกาคู่แรกและคู่สุดท้าย)
                # \s* คือเผื่อมี whitespace
                match = re.search(r"\{[\s\S]*\}", raw_content)
                
                if match:
                    json_str = match.group(0)
                    parsed_json = json.loads(json_str)
                    report_content = json.dumps(parsed_json, indent=4, ensure_ascii=False)
                else:
                    print("⚠️ Market Analyst: No JSON object found via Regex. Falling back to raw text.")
                    # สร้าง JSON หลอกๆ เพื่อให้โปรแกรมไม่พังในขั้นตอนต่อไป
                    fallback_json = {
                        "error": "JSON Parsing Failed",
                        "raw_content": raw_content[:500] + "..." # ตัดให้สั้นลง
                    }
                    report_content = json.dumps(fallback_json)
                
            except Exception as e:
                print(f"⚠️ Market Analyst: Parsing Error ({e}). Saving fallback JSON.")
                report_content = json.dumps({"error": str(e), "raw_content": str(raw_content)[:500]})

        return {
            "messages": [result],
            "market_report": report_content,
        }

    return market_analyst_node