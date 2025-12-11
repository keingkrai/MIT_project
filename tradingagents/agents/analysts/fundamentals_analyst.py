from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json
from tradingagents.agents.utils.agent_utils import get_fundamentals, get_balance_sheet, get_cashflow, get_income_statement, get_insider_sentiment, get_insider_transactions
from tradingagents.dataflows.config import get_config


def create_fundamentals_analyst(llm):
    def fundamentals_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        company_name = state["company_of_interest"]

        tools = [
            get_fundamentals
        ]

        # Get report length from state
        report_length = state.get("report_length", "long")
        
        # Create report style instructions based on length
        if report_length == "short":
            style_instruction = """
**REPORT STYLE - SHORT FORMAT:**
- Write a brief summary using bullet points only
- Keep it concise - maximum 10-15 bullet points total
- Focus on the most important financial metrics and company fundamentals
- Use simple, clear language
- Explain financial terms in plain English
- Format everything as bullet points (no paragraphs)
- Highlight key numbers and what they mean
- NO summary tables needed - just bullet points
"""
        else:
            style_instruction = """
**REPORT STYLE - LONG FORMAT:**
- Write a comprehensive but easy-to-understand report using bullet points
- Cover financial statements, company profile, and financial history
- Use clear, simple language - explain financial terms in plain English
- Break down complex financial concepts into digestible bullet point sections
- Use headings to organize sections, then bullet points under each
- Keep each bullet point short and focused
- NO summary tables needed - use bullet points throughout
"""
        
        system_message = (
            "You are a researcher tasked with analyzing fundamental information over the past week about a company. Please write a report of the company's fundamental information such as financial documents, company profile, basic company financials, and company financial history to gain a full view of the company's fundamental information to inform traders. Must use the available tools: `get_fundamentals` for specific financial statements."
            + style_instruction
            + """
**IMPORTANT WRITING GUIDELINES:**
- Write in plain, simple English that anyone can understand
- Format everything as bullet points - NO paragraphs or tables
- Explain financial terms clearly (e.g., "revenue" = money the company makes, "profit margin" = how much profit per dollar of sales)
- Use analogies to explain complex financial concepts in bullet points
- Focus on what the numbers mean for traders, not just what they are
- Avoid jargon - explain terms like "P/E ratio", "debt-to-equity", "ROE" clearly
- Keep each bullet point short (1-2 sentences maximum)
- Make it easy to scan with clear headings and bullet points
"""
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant, collaborating with other assistants."
                    " Use the provided tools to progress towards answering the question."
                    " If you are unable to fully answer, that's OK; another assistant with different tools"
                    " will help where you left off. Execute what you can to make progress."
                    " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
                    " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
                    " You have access to the following tools: {tool_names}.\n{system_message}"
                    "For your reference, the current date is {current_date}. The company we want to look at is {ticker}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)

        chain = prompt | llm.bind_tools(tools)

        result = chain.invoke(state["messages"])

        report = ""

        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "messages": [result],
            "fundamentals_report": report,
        }

    return fundamentals_analyst_node
