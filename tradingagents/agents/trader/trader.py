import functools
import time
import json


def create_trader(llm, memory):
    def trader_node(state, name):
        company_name = state["company_of_interest"]
        investment_plan = state["investment_plan"]
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        if past_memories:
            for i, rec in enumerate(past_memories, 1):
                past_memory_str += rec["recommendation"] + "\n\n"
        else:
            past_memory_str = "No past memories found."

        context = {
            "role": "user",
            "content": f"Based on a comprehensive analysis by a team of analysts, here is an investment plan tailored for {company_name}. This plan incorporates insights from current technical market trends, macroeconomic indicators, and social media sentiment. Use this plan as a foundation for evaluating your next trading decision.\n\nProposed Investment Plan: {investment_plan}\n\nLeverage these insights to make an informed and strategic decision.",
        }

        # Get report length from state
        report_length = state.get("report_length", "long")
        
        # Create style instructions based on length
        if report_length == "short":
            style_instruction = """
**WRITING STYLE - SHORT FORMAT:**
- Write a brief trading plan using bullet points only
- Keep it concise - maximum 8-10 bullet points
- Use simple, clear language
- Focus on the most important actions and reasoning
- Explain your decision in plain English
- Format everything as bullet points (no paragraphs)
"""
        else:
            style_instruction = """
**WRITING STYLE - LONG FORMAT:**
- Write a comprehensive but easy-to-understand trading plan using bullet points
- Use clear, simple language - avoid jargon
- Explain your reasoning step-by-step in bullet points
- Break down complex trading concepts into simple bullet points
- Use headings to organize sections, then bullet points under each
- Keep each bullet point short and focused
"""
        
        messages = [
            {
                "role": "system",
                "content": f"""You are a trading agent analyzing market data to make investment decisions. Based on your analysis, provide a specific recommendation to buy, sell, or hold. End with a firm decision and always conclude your response with 'FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**' to confirm your recommendation. Do not forget to utilize lessons from past decisions to learn from your mistakes. Here is some reflections from similar situations you traded in and the lessons learned: {past_memory_str}"""
                + style_instruction
                + """
**IMPORTANT: Write in plain, simple English that anyone can understand. Format everything as bullet points - NO paragraphs. Explain your trading decision clearly and avoid technical jargon. Make it easy for humans to understand why you're recommending BUY, SELL, or HOLD. Keep each bullet point short (1-2 sentences maximum)."""
            },
            context,
        ]

        result = llm.invoke(messages)

        return {
            "messages": [result],
            "trader_investment_plan": result.content,
            "sender": name,
        }

    return functools.partial(trader_node, name="Trader")
