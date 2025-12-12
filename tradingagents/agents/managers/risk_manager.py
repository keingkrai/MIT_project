import time
import json


def create_risk_manager(llm, memory):
    def risk_manager_node(state) -> dict:

        company_name = state["company_of_interest"]

        history = state["risk_debate_state"]["history"]
        risk_debate_state = state["risk_debate_state"]
        market_research_report = state["market_report"]
        news_report = state["news_report"]
        fundamentals_report = state["news_report"]
        sentiment_report = state["sentiment_report"]
        trader_plan = state["investment_plan"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"
            
        system_prompt = (
            "You are the Chief Risk Officer and Debate Judge. Your goal is to evaluate the risk debate and the trader's proposed plan to make a final, binding decision. "
            "INSTRUCTIONS: "
            "1. Write a **single, cohesive executive summary**. Do NOT use section headers, bullet points, or numbering lists. "
            "2. Start immediately with the final verdict (BUY, SELL, or HOLD). "
            "3. Synthesize the risk rationale and the **Final Execution Details** into a smooth, professional narrative. "
            "4. Be decisive and precise with numbers."
        )

        prompt = f"""
        Review the Risk Debate and the Trader's Plan to issue the Final Execution Order for {company_name}.

        TRADER PROPOSED PLAN
        {trader_plan}

        RISK ANALYST DEBATE HISTORY
        {history}

        PAST MISTAKES TO AVOID
        {past_memory_str}

        REQUIRED OUTPUT FORMAT
        Provide a comprehensive executive summary (1-2 paragraphs).
        Start by stating the Final Verdict (BUY, SELL, or HOLD) clearly.
        Then, explain the risk rationale based on the debate (referencing the strongest arguments).
        Crucially, you MUST embed the **Final Execution Details** within the narrative, specifically stating:
        - The approved Position Size (percentage)
        - The Entry Price Zone
        - The specific Hard Stop Loss Level
        - The Take Profit Target
        - One critical Safety Protocol (condition to invalidate the trade).
        
        Focus on flow and clarity. No section breaks.
        """
        response = llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ])

        new_risk_debate_state = {
            "judge_decision": response.content,
            "history": risk_debate_state["history"],
            "risky_history": risk_debate_state["risky_history"],
            "safe_history": risk_debate_state["safe_history"],
            "neutral_history": risk_debate_state["neutral_history"],
            "latest_speaker": "Judge",
            "current_risky_response": risk_debate_state["current_risky_response"],
            "current_safe_response": risk_debate_state["current_safe_response"],
            "current_neutral_response": risk_debate_state["current_neutral_response"],
            "count": risk_debate_state["count"],
        }

        return {
            "risk_debate_state": new_risk_debate_state,
            "final_trade_decision": response.content,
        }

    return risk_manager_node
