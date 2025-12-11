from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json
from tradingagents.agents.utils.agent_utils import get_news, get_social
from tradingagents.dataflows.config import get_config


def create_social_media_analyst(llm):
    def social_media_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        company_name = state["company_of_interest"]

        tools = [
            get_social
        ]

        # Get report length from state
        report_length = state.get("report_length", "long")
        
        # Create report style instructions based on length
        if report_length == "short":
            style_instruction = """
**REPORT STYLE - SHORT FORMAT:**
- Write a brief summary using bullet points only
- Keep it concise - maximum 10-15 bullet points total
- Focus on the most important sentiment trends and key social media insights
- Use simple, clear language
- Format everything as bullet points (no paragraphs)
- NO summary tables needed - just bullet points
"""
        else:
            style_instruction = """
**REPORT STYLE - LONG FORMAT:**
- Write a comprehensive but easy-to-understand report using bullet points
- Cover social media sentiment, public opinion, and company news
- Use clear, simple language - explain terms in plain English
- Break down sentiment trends into digestible bullet point sections
- Use headings to organize sections, then bullet points under each
- Keep each bullet point short and focused
- NO summary tables needed - use bullet points throughout
"""
        
        system_message = (
            "You are a social media and company specific news researcher/analyst tasked with analyzing social media posts, recent company news, and public sentiment for a specific company over the past week. You will be given a company's name your objective is to write a report detailing your analysis, insights, and implications for traders and investors on this company's current state after looking at social media and what people are saying about that company, analyzing sentiment data of what people feel each day about the company, and looking at recent company news. Use the get_news(query, start_date, end_date) tool to search for company-specific news and social media discussions. Try to look at all sources possible from social media to sentiment to news."
            + style_instruction
            + """
**IMPORTANT WRITING GUIDELINES:**
- Write in plain, simple English that anyone can understand
- Format everything as bullet points - NO paragraphs or tables
- Explain what sentiment means and why it matters in simple terms
- Use clear examples from social media discussions in bullet points
- Focus on actionable insights for traders
- Avoid jargon - explain terms like "sentiment score" or "engagement rate" clearly
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
                    "For your reference, the current date is {current_date}. The current company we want to analyze is {ticker}",
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
            "sentiment_report": report,
        }

    return social_media_analyst_node
