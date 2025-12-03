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
            "You are a Senior High Risk Equity Researcher. Your goal is to champion high reward opportunities, innovation, and aggressive growth. "
            "You must critique the Conservative and Neutral analysts for being too cautious. "
            "INSTRUCTIONS "
            "1. Write using ONLY plain text. Do not use asterisks, hashes, or dashes. "
            "2. Do NOT use abbreviations. Use full terms (e.g., Return on Investment, Volatility, Year over Year). "
            "3. Focus on the Upside. Argue that fortune favors the bold."
        )

        user_prompt = f"""
        Review the Trader Plan and the Debate to formulate your High Risk argument.

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

        REQUIRED OUTPUT FORMAT
        Section 1 Direct Rebuttal
        Directly counter the fears raised by the Conservative and Neutral analysts. Explain why their caution will lead to missed opportunities.

        Section 2 The Growth Thesis
        Highlight specific data points (Earnings Growth, Hype, Momentum) that justify taking higher risks.

        Section 3 Aggressive Strategy
        Advocate for a decisive position. Suggest that volatility is the price of entry for high returns.
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
