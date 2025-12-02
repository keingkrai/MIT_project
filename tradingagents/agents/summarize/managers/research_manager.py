import openai, os

# ควรสร้าง Client นอกฟังก์ชัน หรือใช้ Singleton เพื่อไม่ให้สร้าง connection ใหม่ทุกครั้งที่เรียก
client = openai.OpenAI(
    api_key=os.getenv("TYPHOON_API_KEY"),
    base_url="https://api.opentyphoon.ai/v1"
)

def create_summarizer_research_manager():
    def research_manager_summarizer(state) -> dict:
        
        # ดึงรายงานเดิมมา
        investment_plan_report = state.get("investment_plan")
        
        # ถ้าไม่มีรายงานเดิม ให้ข้ามไปเลย
        if not investment_plan_report:
            return {} 

        system_prompt = """You are a Senior Investment Strategy Analyst.
Your task is to interpret raw investment plan content and convert it into a concise, 
decision-ready summary suitable for strategic review.

Your analysis must:
- Focus strictly on information contained in the provided investment plan report.
- Identify investment objectives, risk considerations, asset choices, time horizons,
  portfolio rationale, and any supporting evidence or assumptions.
- Highlight strengths, weaknesses, opportunities, and areas of uncertainty.
- Avoid adding external data or making speculative predictions.
- Present insights clearly, professionally, and in a structured format.

Goal: Summarize the investment plan in a way that supports portfolio review, adjustments,
or executive-level decision-making."""
        
        user_prompt = f"""
Synthesize the following investment plan into a concise, structured analytical summary:

=========================================
RAW INVESTMENT PLAN REPORT:
{investment_plan_report}
=========================================

**INSTRUCTIONS:**
- Derive all conclusions strictly from the provided investment plan.
- Identify the plan's structure, rationale, asset strategy, risk logic, 
  assumptions, constraints, and expected outcomes.
- Highlight contradictions, unclear reasoning, or missing foundations.
- Keep the summary clean, structured, and easy to scan.
- Do NOT add external assumptions.

**REQUIRED OUTPUT FORMAT:**

### 1. Investment Plan Overview
- **Objective:** (Return goals, time horizon, strategic intent)
- **Strategy Type:** (e.g., growth, income, balanced, thematic, tactical)
- **Rationale:** (Why this strategy? What principle does it rely on?)

### 2. Key Components of the Plan
- **Asset Allocation:** (Weighting, asset classes, sectors, instruments)
- **Risk Management:** (Hedges, diversification logic, stop-loss, constraints)
- **Supporting Assumptions:** (Market outlook, narrative, catalysts)
- **Time Horizon & Rebalance Approach:** (Short/medium/long-term logic)

### 3. Critical Observations
- **Strengths:** (Clear logic, alignment with goals, diversification quality)
- **Weaknesses / Gaps:** (Missing justification, unclear risk logic, overexposure)
- **Dependencies:** (Factors that may impact success)

### 4. Actionable Insight
- Provide 1–2 neutral, professional recommendations or considerations 
  (e.g., “Evaluate risk concentration,” “Clarify assumption on X,” 
   “Assess whether allocation aligns with time horizon.”)
        """
        
        try:
            response = client.chat.completions.create(
                model="typhoon-v2.1-12b-instruct",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.4,
                max_tokens=1024
            )

            summary_content = response.choices[0].message.content
            
            # ✅ แก้ไขตรงนี้: ใช้ : แทน , และใช้ key เดิมเพื่อ update state
            return {"Summarize_investment_plan_report": summary_content}
        except Exception as e:
            print(f"Error in summarizer: {e}")
            return {} # คืนค่าว่างถ้า error จะได้ไม่พัง
        
    return research_manager_summarizer