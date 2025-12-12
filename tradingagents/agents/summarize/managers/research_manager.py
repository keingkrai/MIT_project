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

        system_prompt = (
            "You are a Senior Investment Strategy Analyst. "
            "Your task is to distill the Investment Plan into a **single, high-density executive summary**. "
            "Do NOT use section headers, bullet points, or lists. "
            "Write in a professional, narrative paragraph format. "
            "Focus on the core decision, execution logic, and risk management."
        )
        
        user_prompt = f"""
        Synthesize the investment plan below into a concise summary (max 150 words).

        =========================================
        RAW INVESTMENT PLAN REPORT:
        {investment_plan_report}
        =========================================

        **INSTRUCTIONS:**
        1. Start immediately with the **Final Decision & Strategic Intent** (e.g., "The plan is to ACCUMULATE based on...").
        2. Seamlessly integrate the **Winning Argument** and **Rationale** (Why this side won?).
        3. Embed the **Execution Details** (Entry zone, Urgency) naturally within the narrative.
        4. Conclude with the **Primary Risk** that would invalidate this plan.
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