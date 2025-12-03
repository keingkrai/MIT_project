import functools
import time
import json


def create_trader(llm, memory):
    def trader_node(state, name):
        company_name = state["company_of_interest"]
        investment_plan = state["investment_plan"]
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        if past_memories:
            for i, rec in enumerate(past_memories, 1):
                past_memory_str += rec["recommendation"] + "\n\n"
        else:
            past_memory_str = "No past memories found."
            
        system_msg = (
            "You are a Senior Head Trader responsible for the final execution decision. "
            "Your job is to audit the proposed plan against raw intelligence reports. "
            "INSTRUCTIONS "
            "1. Write using ONLY plain text. Do not use asterisks, hashes, or dashes. Use numbering like 1, 2, 3. "
            "2. Do NOT use abbreviations. Use full terms (e.g., write Stop Loss instead of SL, Take Profit instead of TP, Moving Average instead of MA). "
            "3. Be decisive. Issue a final execution order."
        )

        user_content = f"""
        Review the Intelligence Reports and the Proposed Plan to make your decision for {company_name}.

        RAW INTELLIGENCE REPORTS
        Market Technicals: {market_research_report}
        Sentiment: {sentiment_report}
        News: {news_report}
        Fundamentals: {fundamentals_report}

        PROPOSED PLAN FROM ANALYSTS
        {investment_plan}

        PAST REFLECTIONS
        {past_memory_str}

        REQUIRED OUTPUT FORMAT
        Section 1 Plan Validation
        Do you agree with the proposed plan? Explain why or why not based on the raw intelligence.

        Section 2 Memory Application
        Explain how past lessons influenced this specific decision.

        Section 3 Final Decision
        Clearly state BUY, SELL, or HOLD.

        Section 4 Execution Details
        Specify the Position Size, Entry Price, and Stop Loss using full terms.

        ENDING
        You MUST conclude with exactly: FINAL TRANSACTION PROPOSAL BUY HOLD SELL
        (Select ONLY ONE word after PROPOSAL).
        """
        
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_content},
        ]

        result = llm.invoke(messages)

        return {
            "messages": [result],
            "trader_investment_plan": result.content,
            "sender": name,
        }

    return functools.partial(trader_node, name="Trader")
