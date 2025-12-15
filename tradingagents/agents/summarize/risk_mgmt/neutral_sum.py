import openai, os

# ควรสร้าง Client นอกฟังก์ชัน หรือใช้ Singleton เพื่อไม่ให้สร้าง connection ใหม่ทุกครั้งที่เรียก
client = openai.OpenAI(
    api_key=os.getenv("TYPHOON_API_KEY"),
    base_url="https://api.opentyphoon.ai/v1"
)

def create_summarizer_neutral():
    def neutral_node_summarizer(state) -> dict:
        
        # ดึงรายงานเดิมมา
        neutral_report = state.get("risk_debate_state").get("neutral_history")
        
        # ถ้าไม่มีรายงานเดิม ให้ข้ามไปเลย
        if not neutral_report:
            return {} 

        system_prompt = (
            "You are a Senior Neutral-Stance Analyst. "
            "Your task is to synthesize the balanced and objective arguments into a **single, high-density executive summary**. "
            "Do NOT use section headers, bullet points, or lists. "
            "Write in a professional, unbiased, and narrative paragraph format. "
            "Focus on the tension between bullish and bearish factors and the rationale for a middle-ground strategy."
        )

        user_prompt = f"""
        Synthesize the neutral debate history below into a concise summary (max 150 words).

        =========================================
        RAW NEUTRAL DEBATE HISTORY:
        {neutral_report}
        =========================================

        **INSTRUCTIONS:**
        1. Start immediately with the **Balanced Verdict** (e.g., "The Neutral view suggests a wait-and-see approach due to...").
        2. Seamlessly integrate the **Conflicting Signals** (Pros vs. Cons) and **Uncertainties** into the narrative.
        3. Explain the **Risk-Reward Tension** naturally within the text.
        4. Conclude with a **Prudent Compromise** (e.g., "Accumulate only on confirmed dips").
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
            return {"Summarize_neutral_report": summary_content}
        except Exception as e:
            print(f"Error in summarizer: {e}")
            return {} # คืนค่าว่างถ้า error จะได้ไม่พัง
        
    return neutral_node_summarizer
