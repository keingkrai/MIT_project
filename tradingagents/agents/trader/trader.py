import functools
import json
from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

# 1. กำหนดโครงสร้างข้อมูลที่ต้องการด้วย Pydantic (Schema Definition)
class PlanValidation(BaseModel):
    agreement_status: str = Field(description="Agree / Disagree / Partial Agreement")
    validation_notes: str = Field(description="Why you agree or disagree based on raw intelligence.")

# class ExecutionDetails(BaseModel):
#     order_type: str = Field(description="Order Type e.g., Market / Limit")
#     position_size_strategy: str = Field(description="e.g., 5 percent of portfolio due to high volatility.")
#     entry_price_target: str = Field(description="Specific price or 'Current Market Price'")
#     stop_loss_level: str = Field(description="Specific price level")
#     take_profit_target: str = Field(description="Specific price level")

class TraderDecision(BaseModel):
    plan_validation: PlanValidation
    memory_application: str = Field(description="Specific lesson applied from past reflections to this trade.")
    final_decision_signal: str = Field(description="BUY / SELL / HOLD")
    # execution_details: ExecutionDetails
    trader_commentary: str = Field(description="Final remarks or warnings for the Risk Manager.")

# --- Function หลัก ---

def create_trader(llm, memory):
    def trader_node(state, name):
        company_name = state.get("company_of_interest", "Unknown Company")
        investment_plan = state.get("investment_plan", "N/A")
        
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

        # 3. Setup Parser (พระเอกของเรา)
        parser = JsonOutputParser(pydantic_object=TraderDecision)

        # 4. System Prompt + Format Instructions (ใส่ format อัตโนมัติ)
        system_msg = (
            "You are a Senior Head Trader. Your job is to audit the investment plan and issue a final execution order.\n"
            "INSTRUCTIONS:\n"
            "1. Audit: Verify the proposed plan against raw intelligence reports.\n"
            "2. Decide: Make a definitive BUY, SELL, or HOLD call.\n"
            "3. No Markdown: Output strictly clean JSON.\n"
            "\n{format_instructions}" 
        )

        # 5. User Prompt
        user_template = """
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
        
        Response needs to follow the JSON schema strictly.
        """

        # สร้าง Prompt Template เพื่อรวม System และ User เข้าด้วยกัน
        prompt = PromptTemplate(
            template=f"{system_msg}\n\n{user_template}",
            input_variables=["company_name", "market_report", "sentiment_report", 
                             "news_report", "fundamentals_report", "investment_plan", "past_memory_str"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )

        # 6. สร้าง Chain และ Invoke (Prompt -> LLM -> Parser)
        # การใช้ | parser จะช่วยตัด Markdown และ Parse string เป็น Dict ให้เลย
        chain = prompt | llm | parser

        try:
            # เรียกใช้งาน Chain
            parsed_result = chain.invoke({
                "company_name": company_name,
                "market_report": market_report,
                "sentiment_report": sentiment_report,
                "news_report": news_report,
                "fundamentals_report": fundamentals_report,
                "investment_plan": investment_plan,
                "past_memory_str": past_memory_str
            })

            # แปลง Dict กลับเป็น JSON String เพื่อเก็บลง State (ตาม Logic เดิม)
            trader_plan_content = json.dumps(parsed_result, indent=4, ensure_ascii=False)

        except Exception as e:
            print(f"⚠️ Trader: Parsing Error ({e}). Attempting fallback recovery...")
            # Fallback กรณีแย่ที่สุด (เช่น Model เอ๋อจนแก้ไม่ได้)
            fallback_data = {
                "final_decision_signal": "HOLD (System Error)",
                "trader_commentary": f"JSON Parsing failed: {str(e)}",
                "plan_validation": {"agreement_status": "Error", "validation_notes": "Parsing failed"},
                "execution_details": {},
                "memory_application": "N/A"
            }
            trader_plan_content = json.dumps(fallback_data, indent=4)

        return {
            # หมายเหตุ: ถ้าต้องการเก็บ raw message อาจต้องปรับ logic นิดหน่อย 
            # แต่ปกติถ้าใช้ parser เราจะเก็บผลลัพธ์สุดท้ายเลย
            "messages": [f"Trader Decision: {parsed_result.get('final_decision_signal', 'Unknown')}"], 
            "trader_investment_plan": trader_plan_content,
            "sender": name,
        }

    return functools.partial(trader_node, name="Trader")