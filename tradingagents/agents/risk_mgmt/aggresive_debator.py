import time
import json


def create_risky_debator(llm):
    def risky_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        risky_history = risk_debate_state.get("risky_history", "")

        current_safe_response = risk_debate_state.get("current_safe_response", "")
        current_neutral_response = risk_debate_state.get("current_neutral_response", "")

        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        trader_decision = state["trader_investment_plan"]
        
        system_prompt = (
            "You are a Senior High Risk Equity Researcher. "
            "Your goal is to champion high reward opportunities, innovation, and aggressive growth. "
            "You must critique the Conservative and Neutral analysts for being too cautious. "
            "INSTRUCTIONS: "
            "1. Write a **single, cohesive argument**. Do NOT use section headers, bullet points, or lists. "
            "2. Write using ONLY plain text. Do not use asterisks, hashes, or dashes. "
            "3. Do NOT use abbreviations. Use full terms. "
            "4. Be bold, persuasive, and focus purely on the upside potential."
        )

        user_prompt = f"""
        Review the Trader Plan and the Debate to formulate your High Risk argument (max 150 words).

        TRADER PLAN
        {trader_decision}

        RAW INTELLIGENCE
        Market Technicals: {market_research_report}
        Sentiment: {sentiment_report}
        News: {news_report}
        Fundamentals: {fundamentals_report}

        DEBATE CONTEXT
        History: {history}
        Conservative Argument: {current_safe_response}
        Neutral Argument: {current_neutral_response}

        **INSTRUCTIONS:**
        1. Start by **Directly Rebutting** the fears raised by the Conservative/Neutral analysts (explain why their caution is a mistake).
        2. Pivot immediately to the **Growth Thesis**, citing specific data (Earnings, Momentum, Hype) that justifies the risk.
        3. Conclude with an **Aggressive Strategy** call (e.g., "Buy now and embrace the volatility").
        4. Maintain a "Fortune favors the bold" tone throughout.
        """

        response = llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])

        argument = f"Risky Analyst: {response.content}"

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "risky_history": risky_history + "\n" + argument,
            "safe_history": risk_debate_state.get("safe_history", ""),
            "neutral_history": risk_debate_state.get("neutral_history", ""),
            "latest_speaker": "Risky",
            "current_risky_response": argument,
            "current_safe_response": risk_debate_state.get("current_safe_response", ""),
            "current_neutral_response": risk_debate_state.get(
                "current_neutral_response", ""
            ),
            "count": risk_debate_state["count"] + 1,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return risky_node
