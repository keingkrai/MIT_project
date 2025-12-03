from langchain_core.messages import AIMessage
import time
import json


def create_safe_debator(llm):
    def safe_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        safe_history = risk_debate_state.get("safe_history", "")

        current_risky_response = risk_debate_state.get("current_risky_response", "")
        current_neutral_response = risk_debate_state.get("current_neutral_response", "")

        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        trader_decision = state["trader_investment_plan"]
        
        system_prompt = (
            "You are a Senior Conservative Risk Analyst. Your number one priority is Capital Preservation. "
            "You are skeptical of hype and high volatility. You must critique the Risky and Neutral analysts for being reckless. "
            "INSTRUCTIONS "
            "1. Write using ONLY plain text. Do not use asterisks, hashes, or dashes. "
            "2. Do NOT use abbreviations. Use full terms (e.g., Maximum Drawdown, Stop Loss, Moving Average). "
            "3. Focus on the Downside. Ask: What if this goes wrong?"
        )

        user_prompt = f"""
        Review the Trader Plan and the Debate to formulate your Conservative argument.

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
        Neutral Argument: {current_neutral_response}

        REQUIRED OUTPUT FORMAT
        Section 1 Direct Rebuttal
        Directly counter the points made by the Risky and Neutral analysts. Explain why their optimism ignores potential dangers.

        Section 2 Worst Case Scenario
        Describe exactly how the trade could fail based on the data (e.g., Economic Recession, Overbought Signals).

        Section 3 Protective Measures
        Propose stricter safety rules. Suggest reducing the Position Size or tightening the Stop Loss.
        """

        response = llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])

        argument = f"Safe Analyst: {response.content}"

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "risky_history": risk_debate_state.get("risky_history", ""),
            "safe_history": safe_history + "\n" + argument,
            "neutral_history": risk_debate_state.get("neutral_history", ""),
            "latest_speaker": "Safe",
            "current_risky_response": risk_debate_state.get(
                "current_risky_response", ""
            ),
            "current_safe_response": argument,
            "current_neutral_response": risk_debate_state.get(
                "current_neutral_response", ""
            ),
            "count": risk_debate_state["count"] + 1,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return safe_node
