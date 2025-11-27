from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json
# from tradingagents.agents.utils.agent_utils import get_indicators
from tradingagents.dataflows.core_indicator import get_indicators
from tradingagents.dataflows.core_stock_price import get_stock_data
from tradingagents.dataflows.config import get_config


def create_market_analyst(llm):

    def market_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        company_name = state["company_of_interest"]

        tools = [
            get_stock_data,
            get_indicators,
        ]

        system_message = (
            """You are a trading assistant tasked with analyzing financial markets. 

    **YOUR WORKFLOW:**
    1. **Retrieve Data:** You MUST call `get_stock_data` first. This tool will compare multiple data providers (Yahoo, TwelveData, etc.) and return the most reliable OHLCV data in CSV format.
    2. **Generate Indicators:** Once you receive the CSV data, examine the market context and select up to **8 relevant indicators** from the list below. Then, call `get_indicators` using the exact codes provided.
    3. **Analyze & Report:** Write a detailed, nuanced report based ONLY on the data retrieved. Do not hallucinate prices.

    **AVAILABLE INDICATORS (Use these exact codes):**
    
    [Moving Averages]
    - close_50_sma, close_200_sma, close_10_ema
    
    [MACD]
    - macd, macds, macdh
    
    [Momentum & Volatility]
    - rsi, boll, boll_ub, boll_lb, atr
    
    [Volume]
    - vwma

    **REPORTING GUIDELINES:**
    - Explain WHY you selected these indicators for the current market context.
    - Provide fine-grained analysis of trends (avoid generic phrases like "trends are mixed").
    - **CRITICAL:** Append a Markdown table at the very end summarizing the key data points and indicator signals.
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
            "market_report": report,
        }

    return market_analyst_node
