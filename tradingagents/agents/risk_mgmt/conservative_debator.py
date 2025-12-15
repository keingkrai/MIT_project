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
            "You are a Senior Conservative Risk Analyst. "
            "Your number one priority is Capital Preservation. "
            "You are skeptical of hype and high volatility. "
            "INSTRUCTIONS: "
            "1. Write a **single, cohesive argument**. Do NOT use section headers, bullet points, or lists. "
            "2. Write using ONLY plain text. Do NOT use abbreviations. "
            "3. Focus on the Downside. Ask: What if this goes wrong?"
        )

        user_prompt = f"""
        Review the Trader Plan and the Debate to formulate your Conservative argument (max 150 words).

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

        **INSTRUCTIONS:**
        1. Start by **Directly Rebutting** the Risky/Neutral analysts (explain why their optimism is dangerous).
        2. Pivot immediately to the **Worst Case Scenario**, citing specific data (e.g., Resistance levels, Economic downturns) that could crash the trade.
        3. Conclude with **Protective Measures**, demanding a reduced Position Size or a tighter Stop Loss to ensure survival.
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
