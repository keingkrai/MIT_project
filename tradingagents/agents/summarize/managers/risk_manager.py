import openai, os

# ควรสร้าง Client นอกฟังก์ชัน หรือใช้ Singleton เพื่อไม่ให้สร้าง connection ใหม่ทุกครั้งที่เรียก
client = openai.OpenAI(
    api_key=os.getenv("TYPHOON_API_KEY"),
    base_url="https://api.opentyphoon.ai/v1"
)

def create_summarizer_risk_manager():
    def risk_manager_summarizer(state) -> dict:
        
        # ดึงรายงานเดิมมา
        final_trade_decision_report = state.get("final_trade_decision")
        
        # ถ้าไม่มีรายงานเดิม ให้ข้ามไปเลย
        if not final_trade_decision_report:
            return {} 

        system_prompt = (
            "You are a Senior Risk Manager. "
            "Your task is to synthesize the Final Trade Decision into a **single, high-density executive summary**. "
            "Do NOT use section headers, bullet points, or lists. "
            "Write in a professional, narrative paragraph format. "
            "Focus on risk exposure, execution constraints, and final approval logic."
        )

        user_prompt = f"""
        Synthesize the final trade decision below into a concise summary (max 150 words).

        =========================================
        RAW FINAL TRADE DECISION REPORT:
        {final_trade_decision_report}
        =========================================

        **INSTRUCTIONS:**
        1. Start immediately with the **Final Risk Verdict** (e.g., "Trade APPROVED for a Long position...", "Trade REJECTED due to...").
        2. Seamlessly integrate the **Risk Rationale** (Why is this safe enough?) and **Conviction Level**.
        3. Embed the **Mandatory Execution Guardrails** (Specific Position Size, Hard Stop Loss, Entry Zone) naturally into the text.
        4. Conclude with the **Critical Invalidating Condition** (The specific safety protocol).
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
            return {"Summarize_final_trade_decision_report": summary_content}
        except Exception as e:
            print(f"Error in summarizer: {e}")
            return {} # คืนค่าว่างถ้า error จะได้ไม่พัง
        
    return risk_manager_summarizer
