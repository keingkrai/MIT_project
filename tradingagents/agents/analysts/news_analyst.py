from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json
from tradingagents.agents.utils.agent_utils import get_news, get_global_news
from tradingagents.dataflows.config import get_config


def create_news_analyst(llm):
    def news_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        tools = [
            get_news,
            get_global_news,
        ]

        # Get report length from state
        report_length = state.get("report_length", "long")
        
        # Create report style instructions based on length
        if report_length == "short":
            style_instruction = """
**REPORT STYLE - SHORT FORMAT:**
- Write a brief summary using bullet points only
- Keep it concise - maximum 10-15 bullet points total
- Focus on the most important news and macroeconomic trends
- Use simple, clear language
- Format everything as bullet points (no paragraphs)
- Highlight key events and their trading implications
- NO summary tables needed - just bullet points
"""
        else:
            style_instruction = """
**REPORT STYLE - LONG FORMAT:**
- Write a comprehensive but easy-to-understand report using bullet points
- Cover relevant news, macroeconomic trends, and global events
- Use clear, simple language - explain economic terms in plain English
- Break down complex economic concepts into digestible bullet point sections
- Use headings to organize sections, then bullet points under each
- Keep each bullet point short and focused
- NO summary tables needed - use bullet points throughout
"""
        
        system_message = (
            "You are a news researcher tasked with analyzing recent news and trends over the past week. Please write a report of the current state of the world that is relevant for trading and macroeconomics. Use the available tools: get_news(query, start_date, end_date) for company-specific or targeted news searches, and get_global_news(curr_date, look_back_days, limit) for broader macroeconomic news."
            + style_instruction
            + """
**IMPORTANT WRITING GUIDELINES:**
- Write in plain, simple English that anyone can understand
- Format everything as bullet points - NO paragraphs or tables
- Explain economic terms and concepts in everyday language
- Use clear examples to illustrate how news affects trading in bullet points
- Focus on what matters most for making trading decisions
- Avoid jargon - explain terms like "inflation", "GDP", "monetary policy" clearly
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
                    "For your reference, the current date is {current_date}. We are looking at the company {ticker}",
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
            "news_report": report,
        }

    return news_analyst_node
