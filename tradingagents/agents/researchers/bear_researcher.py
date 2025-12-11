from langchain_core.messages import AIMessage
import time
import json


def create_bear_researcher(llm, memory):
    def bear_node(state) -> dict:
        investment_debate_state = state["investment_debate_state"]
        history = investment_debate_state.get("history", "")
        bear_history = investment_debate_state.get("bear_history", "")

        current_response = investment_debate_state.get("current_response", "")
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"
            
        system_message = (
            "You are a Senior Bearish Equity Researcher. Your goal is to identify risks, overvaluation, and reasons to SELL. "
            "You must critically debate against the Bullish analyst. "
            "INSTRUCTIONS: "
            "1. Write using ONLY plain text. Do not use asterisks, hashes, or dashes. "
            "2. Do NOT use abbreviations. Use full terms (e.g., Price to Earnings Ratio, Moving Average Convergence Divergence). "
            "3. Be skeptical. Focus on downside protection."
        )

        user_message = f"""
        Review the data and the debate history to formulate your Bearish argument.

        RAW INTELLIGENCE
        Market Technicals: {market_research_report}
        Sentiment: {sentiment_report}
        News: {news_report}
        Fundamentals: {fundamentals_report}

        DEBATE CONTEXT
        History: {history}
        Last Bull Argument: {current_response}

        PAST MISTAKES TO AVOID
        {past_memory_str}

        REQUIRED OUTPUT FORMAT
        Section 1 Direct Rebuttal
        Directly counter the last point made by the Bull analyst. Point out flaws in their logic or data.

        Section 2 Key Risk Factors
        Highlight specific risks (Financial, Technical, or Macroeconomic) that threaten the stock price.

        Section 3 Bearish Conclusion
        State clearly why the stock should be sold or avoided.
        """

        # เรียก LLM (ส่งเป็น List เพื่อแยก Role)
        response = llm.invoke([
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ])

        argument = f"Bear Analyst: {response.content}"

        new_investment_debate_state = {
            "history": history + "\n" + argument,
            "bear_history": bear_history + "\n" + argument,
            "bull_history": investment_debate_state.get("bull_history", ""),
            "current_response": argument,
            "count": investment_debate_state["count"] + 1,
        }

        return {"investment_debate_state": new_investment_debate_state}

    return bear_node
