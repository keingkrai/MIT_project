import openai, os

# ควรสร้าง Client นอกฟังก์ชัน หรือใช้ Singleton เพื่อไม่ให้สร้าง connection ใหม่ทุกครั้งที่เรียก
client = openai.OpenAI(
    api_key=os.getenv("TYPHOON_API_KEY"),
    base_url="https://api.opentyphoon.ai/v1"
)

def create_summarizer_conservative():
    def conservative_node_summarizer(state) -> dict:
        
        # ดึงรายงานเดิมมา
        conservative_report = state.get("risk_debate_state").get("safe_history")
        
        # ถ้าไม่มีรายงานเดิม ให้ข้ามไปเลย
        if not conservative_report:
            return {} 

        system_prompt = (
            "You are a Senior Conservative-Risk Analyst. "
            "Your task is to synthesize the cautious and defensive arguments into a **single, high-density executive summary**. "
            "Do NOT use section headers, bullet points, or lists. "
            "Write in a prudent, risk-averse, and narrative paragraph format. "
            "Focus on capital preservation, downside risks, and uncertainty avoidance."
        )
        
        user_prompt = f"""
        Synthesize the conservative debate history below into a concise summary (max 150 words).

        =========================================
        RAW CONSERVATIVE DEBATE HISTORY:
        {conservative_report}
        =========================================

        **INSTRUCTIONS:**
        1. Start immediately with the **Conservative Stance** (e.g., "The Conservative view strongly advises caution due to...").
        2. Seamlessly integrate **Primary Concerns** (valuations, macro headwinds) and **Defensive Logic** into the narrative.
        3. Highlight the **Fragility** of the current setup naturally within the text.
        4. Conclude with a **Protective Recommendation** (e.g., "Prioritize cash and await better risk-reward").
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
            return {"Summarize_conservative_report": summary_content}
        except Exception as e:
            print(f"Error in summarizer: {e}")
            return {} # คืนค่าว่างถ้า error จะได้ไม่พัง
        
    return conservative_node_summarizer