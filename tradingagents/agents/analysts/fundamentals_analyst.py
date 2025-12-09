from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List
import time
import json
import re

# Import tools
from tradingagents.agents.utils.agent_utils import get_fundamentals, get_balance_sheet, get_cashflow, get_income_statement

def create_fundamentals_analyst(llm):
    
    # --- 1. Define Pydantic Models for JSON Structure ---
    class ComprehensiveMetrics(BaseModel):
        revenue_growth_year_over_year: str = Field(description="The specific percentage growth or decline (e.g., '15 percent').")
        net_profit_margin: str = Field(description="The profitability percentage (e.g., '20 percent').")
        price_to_earnings_ratio: str = Field(description="The current valuation multiple (e.g., '25.5x').")
        debt_to_equity_ratio: str = Field(description="The leverage ratio (e.g., '0.5').")
        return_on_equity: str = Field(description="Efficiency of equity usage (e.g., '18 percent').")
        free_cash_flow_status: str = Field(description="Description of cash generation (e.g., 'Positive and Growing').")

    class FundamentalReport(BaseModel):
        executive_summary: str = Field(description="A detailed paragraph summarizing the company's business model and financial health.")
        valuation_status: str = Field(description="A definitive statement on valuation (e.g., Undervalued / Overvalued).")
        financial_health_score: int = Field(description="An integer from 0 (Bankruptcy Risk) to 100 (Fortress Balance Sheet).")
        comprehensive_metrics: ComprehensiveMetrics = Field(description="Detailed financial metrics object.")
        key_strengths_analysis: List[str] = Field(description="List of detailed explanations of strengths.")
        key_risks_analysis: List[str] = Field(description="List of detailed explanations of risks.")

    # Create Parser
    parser = JsonOutputParser(pydantic_object=FundamentalReport)

    def fundamentals_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        tools = [
            get_fundamentals
        ]

        # --- 2. System Prompt with Format Instructions ---
        system_message = (
            f"""Act as a Senior Fundamental Analyst. Analyze the financial health of **{ticker}**.

    **CRITICAL INSTRUCTION:**
    - You **DO NOT** have current financial data in your internal knowledge.
    - You **MUST CALL** `get_fundamentals` immediately.
    - **Do not** generate any report without calling the tool. If you do not call the tool, you fail.

    **YOUR MANDATORY WORKFLOW:**
    1. **Step 1:** Invoke `get_fundamentals(ticker='{ticker}')`.
    2. **Step 2:** Wait for tool output.
    3. **Step 3:** Output the result strictly in JSON format.

    **STRICT FORMATTING RULES:**
    - **NO ABBREVIATIONS:** Write out every financial term in full (e.g., Price to Earnings Ratio).
    - **No Special Characters:** Avoid *, #, - inside values.
    
    **OUTPUT FORMAT:**
    {parser.get_format_instructions()}
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

        # Call Chain
        result = chain.invoke({"messages": state["messages"]})

        report_content = ""
        
        # --- 3. JSON Parsing Logic ---
        if not result.tool_calls:
            raw_content = result.content
            
            if isinstance(raw_content, list):
                raw_content = " ".join([str(item) for item in raw_content])
            if raw_content is None: raw_content = ""

            try:
                # ลองใช้ Parser ของ LangChain ก่อน (เพราะมันฉลาด)
                parsed_json = parser.parse(raw_content)
                report_content = json.dumps(parsed_json, indent=4, ensure_ascii=False)
                
            except Exception:
                # ถ้า Parser พัง ให้ใช้ไม้ตาย Regex
                try:
                    match = re.search(r"\{[\s\S]*\}", raw_content)
                    if match:
                        json_str = match.group(0)
                        parsed_json = json.loads(json_str)
                        report_content = json.dumps(parsed_json, indent=4, ensure_ascii=False)
                    else:
                        print("⚠️ Fundamental Analyst: No JSON found via Regex.")
                        fallback_json = {"error": "No JSON found", "raw": raw_content[:200]}
                        report_content = json.dumps(fallback_json)
                except Exception as e:
                    print(f"⚠️ Fundamental Analyst: Critical Parsing Error ({e}).")
                    report_content = raw_content

        return {
            "messages": [result],
            "fundamentals_report": report_content,
        }

    return fundamentals_analyst_node