import time
import json
from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

class RiskManagerOutput(BaseModel):
    recommendation: Literal["BUY", "SELL", "HOLD"] = Field(description="The final decision")
    reasoning: str = Field(description="Detailed reasoning anchored in the debate and past reflections")
    refined_trader_plan: str = Field(description="The final approved execution plan (Entry, Stop Loss, Position Size, etc.)")

def create_risk_manager(llm, memory):
    def risk_manager_node(state) -> dict:

        company_name = state["company_of_interest"]

        history = state["risk_debate_state"]["history"]
        risk_debate_state = state["risk_debate_state"]
        market_research_report = state["market_report"]
        news_report = state["news_report"]
        
        fundamentals_report = state.get("fundamentals_report", "") 
        sentiment_report = state["sentiment_report"]
        trader_plan = state["investment_plan"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        if past_memories:
            for i, rec in enumerate(past_memories, 1):
                past_memory_str += rec["recommendation"] + "\n\n"

        parser = JsonOutputParser(pydantic_object=RiskManagerOutput)

        base_prompt = """As the Risk Management Judge and Debate Facilitator, your goal is to evaluate the debate between three risk analysts—Risky, Neutral, and Safe/Conservative—and determine the best course of action for the trader. Your decision must result in a clear recommendation: Buy, Sell, or Hold. Choose Hold only if strongly justified by specific arguments, not as a fallback when all sides seem valid. Strive for clarity and decisiveness.

                Guidelines for Decision-Making:
                1. **Summarize Key Arguments**: Extract the strongest points from each analyst, focusing on relevance to the context.
                2. **Provide Rationale**: Support your recommendation with direct quotes and counterarguments from the debate.
                3. **Refine the Trader's Plan**: Start with the trader's original plan, **{trader_plan}**, and adjust it based on the analysts' insights.
                4. **Learn from Past Mistakes**: Use lessons from **{past_memory_str}** to address prior misjudgments and improve the decision you are making now to make sure you don't make a wrong BUY/SELL/HOLD call that loses money.

                Deliverables:
                - A clear and actionable recommendation: Buy, Sell, or Hold.
                - Detailed reasoning anchored in the debate and past reflections.

                ---

                **Analysts Debate History:** {history}

                ---

                Focus on actionable insights and continuous improvement. Build on past lessons, critically evaluate all perspectives, and ensure each decision advances better outcomes."""
        
        final_prompt_str = base_prompt + "\n\nIMPORTANT: Your response must be in strict JSON format based on the following schema:\n{format_instructions}"
        
        prompt_template = PromptTemplate(
            template=final_prompt_str,
            input_variables=["trader_plan", "past_memory_str", "history"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )
        
        chain = prompt_template | llm | parser

        try:
            # Invoke Chain
            parsed_result = chain.invoke({
                "trader_plan": trader_plan,
                "history": history,
                "past_memory_str": past_memory_str
            })
            
            # แปลง Dict กลับเป็น JSON String เพื่อเก็บลง State (ตาม Logic เดิมที่ระบบอื่นอาจจะรอรับ String)
            final_output_str = json.dumps(parsed_result, indent=4, ensure_ascii=False)
            
        except Exception as e:
            print(f"⚠️ Risk Manager Parsing Error: {e}")
            # Fallback กรณี Parse ไม่ผ่าน ให้สร้าง JSON structure เปล่าๆ กันโปรแกรมพัง
            fallback = {
                "recommendation": "HOLD (Parsing Error)",
                "reasoning": f"Failed to parse output. Raw error: {str(e)}",
                "refined_trader_plan": trader_plan
            }
            final_output_str = json.dumps(fallback, indent=4)

        new_risk_debate_state = {
            "judge_decision": final_output_str,
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
            "final_trade_decision": final_output_str,
        }

    return risk_manager_node