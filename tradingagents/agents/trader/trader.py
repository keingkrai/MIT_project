import functools
import time
import json
import re

def create_trader(llm, memory):
    def trader_node(state, name):
        company_name = state["company_of_interest"]
        investment_plan = state["investment_plan"]
        
        # 1. ดึงรายงานดิบทั้งหมด
        market_report = state.get("market_report", "N/A")
        sentiment_report = state.get("sentiment_report", "N/A")
        news_report = state.get("news_report", "N/A")
        fundamentals_report = state.get("fundamentals_report", "N/A")

        # 2. ค้นหา Memory
        curr_situation = f"{market_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        if past_memories:
            for i, rec in enumerate(past_memories, 1):
                past_memory_str += f"Situation {i}: {rec.get('situation_summary', 'N/A')}\nLesson: {rec['recommendation']}\n"
        else:
            past_memory_str = "No relevant past memories found."

        # 3. JSON System Prompt
        system_msg = (
            "You are a Senior Head Trader. Your job is to audit the investment plan and issue a final execution order in **JSON format**.\n"
            "**INSTRUCTIONS:**\n"
            "1. **Audit:** Verify the proposed plan against raw intelligence reports.\n"
            "2. **Decide:** Make a definitive BUY, SELL, or HOLD call.\n"
            "3. **Format:** Return strictly valid JSON. No markdown code blocks.\n"
            "4. **No Abbreviations:** Use full terms (e.g., 'Stop Loss', 'Take Profit')."
        )

        # 4. User Prompt with JSON Structure
        user_content = f"""
        Review the Intelligence Reports and the Proposed Plan to make your decision for {company_name}.

        RAW INTELLIGENCE REPORTS
        Market Technicals: {market_report}
        Sentiment: {sentiment_report}
        News: {news_report}
        Fundamentals: {fundamentals_report}

        PROPOSED PLAN FROM ANALYSTS
        {investment_plan}

        PAST REFLECTIONS
        {past_memory_str}
        
        IMPORTANT
        - Must json format only.

        **REQUIRED JSON STRUCTURE:**
        {{
            "plan_validation": {{
                "agreement_status": "String: Agree / Disagree / Partial Agreement",
                "validation_notes": "String: Why you agree or disagree based on raw intelligence."
            }},
            "memory_application": "String: Specific lesson applied from past reflections to this trade.",
            "final_decision_signal": "String: BUY / SELL / HOLD",
            "execution_details": {{
                "order_type": "String: e.g., Market / Limit",
                "position_size_strategy": "String: e.g., 5 percent of portfolio due to high volatility.",
                "entry_price_target": "String: Specific price or 'Current Market Price'",
                "stop_loss_level": "String: Specific price level",
                "take_profit_target": "String: Specific price level"
            }},
            "trader_commentary": "String: Final remarks or warnings for the Risk Manager."
        }}
        """

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
<<<<<<< HEAD
            {
                "role": "system",
                "content": f"""You are a trading agent analyzing market data to make investment decisions. Based on your analysis, provide a specific recommendation to buy, sell, or hold. End with a firm decision and always conclude your response with 'FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**' to confirm your recommendation. Do not forget to utilize lessons from past decisions to learn from your mistakes. Here is some reflections from similar situations you traded in and the lessons learned: {past_memory_str}"""
                + style_instruction
                + """
**IMPORTANT: Write in plain, simple English that anyone can understand. Format everything as bullet points - NO paragraphs. Explain your trading decision clearly and avoid technical jargon. Make it easy for humans to understand why you're recommending BUY, SELL, or HOLD. Keep each bullet point short (1-2 sentences maximum)."""
            },
            context,
=======
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_content},
>>>>>>> tang
        ]

        result = llm.invoke(messages)
        
        trader_plan_content = ""

        # --- 5. JSON Parsing Logic ---
        try:
            raw_content = result.content
            # Clean markdown if present
            clean_content = raw_content.strip()
            if clean_content.startswith("```json"):
                clean_content = clean_content[7:]
            elif clean_content.startswith("```"):
                clean_content = clean_content[3:]
            if clean_content.endswith("```"):
                clean_content = clean_content[:-3]
            
            # Regex Extraction
            match = re.search(r"\{[\s\S]*\}", clean_content)
            if match:
                json_str = match.group(0)
                parsed_json = json.loads(json_str)
                trader_plan_content = json.dumps(parsed_json, indent=4, ensure_ascii=False)
            else:
                print("⚠️ Trader: No JSON found. Using raw text.")
                # Fallback structure
                trader_plan_content = json.dumps({
                    "final_decision_signal": "HOLD (Parsing Error)",
                    "trader_commentary": raw_content
                }, indent=4)
                
        except Exception as e:
            print(f"⚠️ Trader: JSON Parse Error ({e}). Saving raw content.")
            trader_plan_content = result.content

        return {
            "messages": [result],
            "trader_investment_plan": trader_plan_content, # เก็บ JSON String
            "sender": name,
        }

    return functools.partial(trader_node, name="Trader")