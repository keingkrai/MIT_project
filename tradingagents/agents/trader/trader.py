import functools
import time
import json
import re
from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

class PlanValidation(BaseModel):
    agreement_status: str = Field(description="Agree / Disagree / Partial Agreement")
    validation_notes: str = Field(description="Why you agree or disagree based on raw intelligence.")

class ExecutionDetails(BaseModel):
    order_type: str = Field(description="Order Type e.g., Market / Limit")
    position_size_strategy: str = Field(description="e.g., 5 percent of portfolio due to high volatility.")
    entry_price_target: str = Field(description="Specific price or 'Current Market Price'")
    stop_loss_level: str = Field(description="Specific price level")
    take_profit_target: str = Field(description="Specific price level")

class TraderDecision(BaseModel):
    plan_validation: PlanValidation
    memory_application: str = Field(description="Specific lesson applied from past reflections to this trade.")
    final_decision_signal: Literal["BUY", "SELL", "HOLD"] = Field(description="decision signal")
    execution_details: ExecutionDetails
    trader_commentary: str = Field(description="Final remarks or warnings for the Risk Manager.") 

def create_trader(llm, memory):
    def trader_node(state, name):
        company_name = state["company_of_interest"]
        investment_plan = state["investment_plan"]

        market_report = state.get("market_report", "N/A")
        sentiment_report = state.get("sentiment_report", "N/A")
        news_report = state.get("news_report", "N/A")
        fundamentals_report = state.get("fundamentals_report", "N/A")

        curr_situation = f"{market_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        if past_memories:
            for i, rec in enumerate(past_memories, 1):
                past_memory_str += f"Situation {i}: {rec.get('situation_summary', 'N/A')}\nLesson: {rec['recommendation']}\n"
        else:
            past_memory_str = "No relevant past memories found."
            
        parser = JsonOutputParser(pydantic_object=TraderDecision)

        system_msg = (
            "You are a Senior Head Trader. Your job is to audit the investment plan and issue a final execution order.\n"
            "INSTRUCTIONS:\n"
            "1. Audit: Verify the proposed plan against raw intelligence reports.\n"
            "2. Decide: Make a definitive BUY, SELL, or HOLD call.\n"
            "3. No Markdown: Output strictly clean JSON.\n"
            "\n{format_instructions}" 
        )

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
        
        OUTPUT FORMAT:
        {parser.get_format_instructions()}
        Response needs to follow the JSON schema strictly.
        """

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_content},
        ]

        result = llm.invoke(messages)
        
        trader_plan_content = ""

        try:
            raw_content = result.content
            clean_content = raw_content.strip()
            if clean_content.startswith("```json"):
                clean_content = clean_content[7:]
            elif clean_content.startswith("```"):
                clean_content = clean_content[3:]
            if clean_content.endswith("```"):
                clean_content = clean_content[:-3]
            
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