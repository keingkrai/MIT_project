from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json
import re # <--- ต้องมี

# Import tools
from tradingagents.agents.utils.agent_utils import get_fundamentals, get_balance_sheet, get_cashflow, get_income_statement

def create_fundamentals_analyst(llm):
    def fundamentals_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        tools = [
            get_fundamentals
        ]

        # --- Prompt ---
        system_message = (
            """Act as a Senior Fundamental Analyst. Analyze the financial health of the company and output the result strictly in **JSON format**.

    **INSTRUCTIONS:**
    1. Use `get_fundamentals` and other tools to gather data.
    2. **OUTPUT FORMAT:** You must return a valid JSON object with the exact keys listed below. 
    3. **NO MARKDOWN:** Do not wrap the output in markdown code blocks. Just return the raw JSON string.
    4. **CONTENT RULES:** Use full names for metrics (e.g., "Price to Earnings Ratio" not "P/E").

    **Output JSON ONLY.**
    
    **JSON STRUCTURE:**
    {
        "executive_summary": "String",
        "valuation_status": "String",
        "financial_health_score": 0,
        "comprehensive_metrics": {
            "revenue_growth_year_over_year": "String",
            "net_profit_margin": "String",
            "price_to_earnings_ratio": "String",
            "debt_to_equity_ratio": "String",
            "return_on_equity": "String",
            "free_cash_flow_status": "String"
        },
        "key_strengths_analysis": [ "String" ],
        "key_risks_analysis": [ "String" ]
    }
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

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)

        chain = prompt | llm.bind_tools(tools)

        result = chain.invoke({"messages": state["messages"]})

        report_content = ""
        
        # --- ✅ Improved JSON Parsing Logic with Debug ---
        if not result.tool_calls:
            raw_content = result.content
            
            # แปลง List เป็น String (กันเหนียว)
            if isinstance(raw_content, list):
                raw_content = " ".join([str(item) for item in raw_content])
            if raw_content is None:
                raw_content = ""

            # 🚨 DEBUG: ปริ้นท์ออกมาดูเลยว่า AI ส่งอะไรมา
            # print(f"\n🔍 DEBUG FUNDAMENTAL RAW:\n{raw_content}\n{'='*30}")

            try:
                # ใช้ Regex หา JSON Object {...}
                match = re.search(r"\{[\s\S]*\}", raw_content)
                
                if match:
                    json_str = match.group(0)
                    parsed_json = json.loads(json_str)
                    report_content = json.dumps(parsed_json, indent=4, ensure_ascii=False)
                else:
                    print("⚠️ Fundamental Analyst: No JSON object found via Regex.")
                    # สร้าง JSON หลอกๆ กันโปรแกรมพัง
                    report_content = json.dumps({
                        "error": "Parsing Failed", 
                        "raw_content": raw_content[:500]
                    })
                
            except Exception as e:
                print(f"⚠️ Fundamental Analyst: Parsing Error ({e}). Saving raw text.")
                report_content = raw_content

        return {
            "messages": [result],
            "fundamentals_report": report_content,
        }

    return fundamentals_analyst_node