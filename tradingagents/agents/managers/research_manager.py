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

        # Get report length from state
        report_length = state.get("report_length", "long")
        
        # Create style instructions based on length
        if report_length == "short":
            style_instruction = """
**WRITING STYLE - SHORT FORMAT:**
- Write a brief investment plan using bullet points only
- Keep it concise - maximum 8-10 bullet points
- Use simple, clear language
- Focus on the most important decision and reasoning
- Explain your recommendation in plain English
- Format everything as bullet points (no paragraphs)
"""
        else:
            style_instruction = """
**WRITING STYLE - LONG FORMAT:**
- Write a comprehensive but easy-to-understand investment plan using bullet points
- Use clear, simple language - avoid jargon
- Explain your reasoning step-by-step in bullet points
- Break down complex investment concepts into simple bullet points
- Use headings to organize sections, then bullet points under each
- Keep each bullet point short and focused
"""
        
        prompt = (
            f"""As the portfolio manager and debate facilitator, your role is to critically evaluate this round of debate and make a definitive decision: align with the bear analyst, the bull analyst, or choose Hold only if it is strongly justified based on the arguments presented.

Summarize the key points from both sides concisely, focusing on the most compelling evidence or reasoning. Your recommendation—Buy, Sell, or Hold—must be clear and actionable. Avoid defaulting to Hold simply because both sides have valid points; commit to a stance grounded in the debate's strongest arguments.

Additionally, develop an investment plan for the trader. This should include:

Your Recommendation: A decisive stance supported by the most convincing arguments.
Rationale: An explanation of why these arguments lead to your conclusion.
Strategic Actions: Concrete steps for implementing the recommendation.
Take into account your past mistakes on similar situations. Use these insights to refine your decision-making and ensure you are learning and improving."""
            + style_instruction
            + f"""
**IMPORTANT: Write in plain, simple English that anyone can understand. Format everything as bullet points - NO paragraphs. Explain your investment decision clearly and avoid jargon. Make it easy for humans to understand why you're recommending BUY, SELL, or HOLD. Keep each bullet point short (1-2 sentences maximum).**

Here are your past reflections on mistakes:
\"{past_memory_str}\"

Here is the debate:
Debate History:
{history}"""
        )
        response = llm.invoke(prompt)

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
