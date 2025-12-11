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
            "1. Write using ONLY plain text. Do not use asterisks, hashes, bullet points, or dashes. Use numbering like 1, 2, 3 or Section headers. "
            "2. Do NOT use abbreviations. Use full terms (e.g., write Stop Loss instead of SL, Position Size instead of Size, Volatility instead of Vol). "
            "3. Prioritize capital preservation but do not be paralyzed by fear. If the reward outweighs the risk, approve the trade with guardrails."
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
        Section 1 Final Verdict
        State clearly: BUY, SELL, or HOLD. This is the final command.

        Section 2 Risk Rationale
        Summarize why you chose this verdict based on the debate. Mention which analyst (Risky, Neutral, or Safe) provided the most convincing argument.

        Section 3 Final Execution Details
        Refine the trader's plan. You must specify:
        1. Approved Position Size (e.g., 5 percent of portfolio).
        2. Entry Price Zone.
        3. Hard Stop Loss Level (Must be specific).
        4. Take Profit Target.

        Section 4 Safety Protocol
        State one specific condition that would invalidate this trade immediately (e.g., if earnings miss expectations or if price drops below a certain moving average).
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
