from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json
import re

# Import tools (ตรวจสอบ path ของคุณให้ถูกต้อง)
from tradingagents.agents.utils.agent_utils import get_fundamentals, get_balance_sheet, get_cashflow, get_income_statement

def create_fundamentals_analyst(llm):
    def fundamentals_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        tools = [
            get_fundamentals
        ]

        system_message = (
            f"""Act as a Senior Fundamental Analyst. Analyze the financial health of **{ticker}**.

    **CRITICAL INSTRUCTION:**
    - You **DO NOT** have current financial data in your internal knowledge.
    - You **MUST CALL** `get_fundamentals` immediately.
    - **Do not** generate any report without calling the tool. If you do not call the tool, you fail.

    **YOUR MANDATORY WORKFLOW:**
    1. **Step 1:** Invoke `get_fundamentals`.
    2. **Step 2:** Wait for tool output.
    3. **Step 3:** Output the result strictly in **JSON format**.

    **STRICT FORMATTING RULES:**
    - **Output JSON ONLY:** Return a raw JSON object. Do not wrap it in markdown.
    - **NO ABBREVIATIONS:** Write out every financial term in full (e.g., Price to Earnings Ratio).
    - **No Special Characters:** Avoid *, #, - inside values.

    **REQUIRED JSON STRUCTURE:**
    {{
        "executive_summary": "String: A detailed paragraph summarizing the company's business model and financial health.",
        "valuation_status": "String: A definitive statement on valuation (e.g., Undervalued / Overvalued).",
        "financial_health_score": "Number: 0-100",
        "comprehensive_metrics": {{
            "revenue_growth_year_over_year": "String",
            "net_profit_margin": "String",
            "price_to_earnings_ratio": "String",
            "debt_to_equity_ratio": "String",
            "return_on_equity": "String",
            "free_cash_flow_status": "String"
        }},
        "key_strengths_analysis": [ "String" ],
        "key_risks_analysis": [ "String" ]
    }}
    """
        )

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

        # เรียก Chain (ส่งเป็น dict แก้บั๊ก langchain)
        result = chain.invoke({"messages": state["messages"]})

        report_content = ""
        
        # --- ⚡ JSON Parsing Logic ---
        if not result.tool_calls:
            raw_content = result.content
            
            # Clean list to string
            if isinstance(raw_content, list):
                raw_content = " ".join([str(item) for item in raw_content])
            if raw_content is None: raw_content = ""

            try:
                # Regex Extraction (หาปีกกาคู่แรกและสุดท้าย)
                match = re.search(r"\{[\s\S]*\}", raw_content)
                
                if match:
                    json_str = match.group(0)
                    parsed_json = json.loads(json_str)
                    report_content = json.dumps(parsed_json, indent=4, ensure_ascii=False)
                else:
                    print("⚠️ Fundamental Analyst: No JSON object found via Regex.")
                    # Fallback: สร้าง JSON เปล่าๆ เพื่อไม่ให้โปรแกรมพัง
                    fallback_json = {
                        "error": "No JSON found",
                        "raw_content": raw_content[:200]
                    }
                    report_content = json.dumps(fallback_json)

            except Exception as e:
                print(f"⚠️ Fundamental Analyst: Parsing Error ({e}). Saving raw text.")
                report_content = raw_content

        return {
            "messages": [result],
            "fundamentals_report": report_content,
        }

    return fundamentals_analyst_node