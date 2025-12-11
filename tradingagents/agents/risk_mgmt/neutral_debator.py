import time
import json


def create_neutral_debator(llm):
    def neutral_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        neutral_history = risk_debate_state.get("neutral_history", "")

        current_risky_response = risk_debate_state.get("current_risky_response", "")
        current_safe_response = risk_debate_state.get("current_safe_response", "")

        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        trader_decision = state["trader_investment_plan"]
        
        system_prompt = (
            "You are a Senior Neutral Risk Analyst. Your goal is to find the balanced 'Golden Mean' between risk and safety. "
            "You must critique the Risky analyst for recklessness and the Conservative analyst for paralysis. "
            "INSTRUCTIONS "
            "1. Write using ONLY plain text. Do not use asterisks, hashes, or dashes. "
            "2. Do NOT use abbreviations. Use full terms (e.g., Standard Deviation, Profit and Loss). "
            "3. Focus on Risk-Adjusted Returns. Propose a sensible middle ground."
        )

        user_prompt = f"""
        Review the Trader Plan and the Debate to formulate your Balanced argument.

        TRADER PLAN
        {trader_decision}

        RAW INTELLIGENCE
        Market Technicals: {market_research_report}
        Sentiment: {sentiment_report}
        News: {news_report}
        Fundamentals: {fundamentals_report}

        DEBATE CONTEXT
        History: {history}
        Risky Argument: {current_risky_response}
        Safe Argument: {current_safe_response}

        REQUIRED OUTPUT FORMAT
        Section 1 Balanced Rebuttal
        Critique both sides. Explain why the Risky approach is too dangerous AND why the Safe approach leaves too much money on the table.

        Section 2 Risk Adjusted Analysis
        Analyze the data to show where the real opportunity lies without exposing capital to ruin.

        Section 3 Strategic Compromise
        Propose a modified plan. For example, suggest a medium Position Size or a wider Stop Loss to allow for volatility.
        """
        response = llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])

        argument = f"Neutral Analyst: {response.content}"

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "risky_history": risk_debate_state.get("risky_history", ""),
            "safe_history": risk_debate_state.get("safe_history", ""),
            "neutral_history": neutral_history + "\n" + argument,
            "latest_speaker": "Neutral",
            "current_risky_response": risk_debate_state.get(
                "current_risky_response", ""
            ),
            "current_safe_response": risk_debate_state.get("current_safe_response", ""),
            "current_neutral_response": argument,
            "count": risk_debate_state["count"] + 1,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return neutral_node
