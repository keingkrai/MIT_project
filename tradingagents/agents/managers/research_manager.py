import time
import json


def create_research_manager(llm, memory):
    def research_manager_node(state) -> dict:
        history = state["investment_debate_state"].get("history", "")
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        investment_debate_state = state["investment_debate_state"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"
            
        system_prompt = (
            "You are the Chief Investment Officer. Your role is to adjudicate the debate between the Bullish and Bearish researchers and make a final investment decision. "
            "INSTRUCTIONS: "
            "1. Write using ONLY plain text. Do not use asterisks, hashes, or dashes. "
            "2. Do NOT use abbreviations. Use full terms (e.g., Price to Earnings Ratio, Simple Moving Average). "
            "3. Be decisive. Do not hedge. Choose Buy, Sell, or Hold based on the strongest evidence."
        )

        prompt = f"""
        Review the following Debate and Past Lessons to form an Investment Plan:

        DEBATE HISTORY
        {history}

        PAST REFLECTIONS
        {past_memory_str}

        REQUIRED OUTPUT FORMAT
        Provide a comprehensive executive summary (1-2 paragraphs). 
        Start by stating the verdict (BUY, SELL, or HOLD) clearly. 
        Then, immediately explain the logic by highlighting the most compelling evidence from the debate, the specific execution strategy (entry/exit urgency), and the critical risk to monitor. 
        Focus only on the core insights and the decision logic. No fluff, no formatting structure.
        """
        
        response = llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ])

        new_investment_debate_state = {
            "judge_decision": response.content,
            "history": investment_debate_state.get("history", ""),
            "bear_history": investment_debate_state.get("bear_history", ""),
            "bull_history": investment_debate_state.get("bull_history", ""),
            "current_response": response.content,
            "count": investment_debate_state["count"],
        }

        return {
            "investment_debate_state": new_investment_debate_state,
            "investment_plan": response.content,
        }

    return research_manager_node
