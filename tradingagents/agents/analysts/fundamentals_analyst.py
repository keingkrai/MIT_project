import json
import re
from typing import List
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser

from tradingagents.agents.utils.agent_utils import (
    get_fundamentals,
    get_balance_sheet,
    get_cashflow,
    get_income_statement
)


# ===================== PYDANTIC MODELS ======================
class ComprehensiveMetrics(BaseModel):
    revenue_growth_year_over_year: str = Field(description="The specific percentage growth or decline (percentage)(e.g., '15').")
    net_profit_margin: str = Field(description="The profitability percentage (e.g., '20').")
    price_to_earnings_ratio: str = Field(description="The current valuation multiple (e.g., '25.5').")
    debt_to_equity_ratio: str = Field(description="The leverage ratio (e.g., '0.5').")
    return_on_equity: str = Field(description="Efficiency of equity usage (percentage)(e.g., '18').")
    free_cash_flow_status: str = Field(description="Description of cash generation (e.g., 'Positive and Growing').")


class FundamentalReport(BaseModel):
    executive_summary: str = Field(description="A detailed paragraph summarizing the company's business model and financial health.")
    valuation_status: str = Field(description="A definitive statement on valuation (e.g., Undervalued / Overvalued / Fairly Valued).")
    comprehensive_metrics: ComprehensiveMetrics = Field(description="Detailed financial metrics object.")
    key_strengths_analysis: List[str] = Field(description="List of detailed explanations of strengths.")
    key_risks_analysis: List[str] = Field(description="List of detailed explanations of risks.")


# ===================== AGENT FACTORY ======================
def create_fundamentals_analyst(llm):
    parser = JsonOutputParser(pydantic_object=FundamentalReport)

    def fundamentals_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        tools = [
            get_fundamentals,
            # get_balance_sheet,
            # get_cashflow,
            # get_income_statement
        ]

        # ===================== SYSTEM MESSAGE ======================
        system_message = f"""
            Act as a Senior Fundamental Analyst specializing in financial statement analysis and company valuation.

            **CRITICAL INSTRUCTION:**
            - You **DO NOT** have current financial data in your internal knowledge.
            - You **MUST CALL** `get_fundamentals(ticker='{ticker}')` immediately to retrieve real data.
            - **DO NOT** generate any report without calling at least `get_fundamentals` first.

            **MANDATORY WORKFLOW:**
            1. Call `get_fundamentals(ticker='{ticker}')` to get comprehensive financial metrics.
            2. Analyze the data thoroughly.
            3. Output the result strictly in JSON format.

            **ANALYSIS GUIDELINES:**
            - Focus on long-term financial health and sustainability
            - Compare metrics to industry averages when relevant
            - Assess both growth potential and downside risks
            - Consider debt levels, profitability, and cash generation

            **FINANCIAL HEALTH SCORE GUIDE:**
            - 0-20: Severe Financial Distress / Bankruptcy Risk
            - 21-40: Weak Financial Position / High Risk
            - 41-60: Average Financial Health / Moderate Risk
            - 61-80: Strong Financial Position / Low Risk
            - 81-100: Exceptional Financial Strength / Fortress Balance Sheet

            **STRICT FORMATTING RULES:**
            - **NO ABBREVIATIONS:** Write out every financial term in full (e.g., Price to Earnings Ratio, not P/E).
            - **NO SPECIAL CHARACTERS:** Avoid *, #, -, or bullet points inside JSON values.
            - Use plain language without markdown formatting.

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
                "The company we want to look at is {ticker}."
            ),
            MessagesPlaceholder(variable_name="messages"),
        ])

        prompt = prompt.partial(
            system_message=system_message,
            tool_names=", ".join([tool.name for tool in tools]),
            current_date=current_date,
            ticker=ticker
        )

        # ===================== CHAIN ======================
        chain = prompt | llm.bind_tools(tools)

        # Execute
        result = chain.invoke(state["messages"])
        
        print("Fundamentals Analysis Result:", result)

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
                        report_dict = FundamentalReport.model_validate(report_dict).model_dump()
                    else:
                        print("⚠️ No JSON object found in response")
                        # Create minimal valid fallback
                        report_dict = {
                            "executive_summary": "Unable to retrieve fundamental data for analysis.",
                            "valuation_status": "Unknown (Data Unavailable)",
                            "financial_health_score": 50,
                            "comprehensive_metrics": {
                                "revenue_growth_year_over_year": "Data unavailable",
                                "net_profit_margin": "Data unavailable",
                                "price_to_earnings_ratio": "Data unavailable",
                                "debt_to_equity_ratio": "Data unavailable",
                                "return_on_equity": "Data unavailable",
                                "free_cash_flow_status": "Data unavailable"
                            },
                            "key_strengths_analysis": ["Data retrieval error - unable to assess strengths"],
                            "key_risks_analysis": ["Data retrieval error - unable to assess risks"]
                        }
                        
                except Exception as e2:
                    print(f"⚠️ Fallback parsing failed: {e2}")
                    report_dict = {
                        "executive_summary": "Error occurred during fundamental analysis.",
                        "valuation_status": "Error",
                        "financial_health_score": 50,
                        "comprehensive_metrics": {
                            "revenue_growth_year_over_year": "Error",
                            "net_profit_margin": "Error",
                            "price_to_earnings_ratio": "Error",
                            "debt_to_equity_ratio": "Error",
                            "return_on_equity": "Error",
                            "free_cash_flow_status": "Error"
                        },
                        "key_strengths_analysis": ["Analysis error occurred"],
                        "key_risks_analysis": ["Analysis error occurred"]
                    }
        
        # If still None (tool_calls present), create waiting structure
        if report_dict is None:
            report_dict = {"status": "waiting_for_tool_response"}

        # Convert dict to JSON string
        report_json = json.dumps(report_dict, indent=4, ensure_ascii=False)

        return {
            "messages": [result],
            "fundamentals_report": report_json,  # Return as JSON string
        }

    return fundamentals_analyst_node