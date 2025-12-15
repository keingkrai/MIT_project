import openai, os

# ควรสร้าง Client นอกฟังก์ชัน หรือใช้ Singleton เพื่อไม่ให้สร้าง connection ใหม่ทุกครั้งที่เรียก
client = openai.OpenAI(
    api_key=os.getenv("TYPHOON_API_KEY"),
    base_url="https://api.opentyphoon.ai/v1"
)

def create_summarizer_aggressive():
    def aggressive_node_summarizer(state) -> dict:

        # ดึงรายงานเดิมมา
        aggressive_report = state.get("risk_debate_state").get("risky_history")
        
        # ถ้าไม่มีรายงานเดิม ให้ข้ามไปเลย
        if not aggressive_report:
            return {} 

        system_prompt = (
            "You are a Senior Aggressive Strategy Analyst. "
            "Your task is to synthesize the high-risk/speculative arguments into a **single, high-density executive summary**. "
            "Do NOT use section headers, bullet points, or lists. "
            "Write in a bold, narrative paragraph format. "
            "Focus on momentum, speculative catalysts, and asymmetric upside opportunities."
        )

        user_prompt = f"""
        Synthesize the aggressive debate history below into a concise summary (max 150 words).

        =========================================
        RAW RISK & AGGRESSIVE DEBATE HISTORY:
        {aggressive_report}
        =========================================

        **INSTRUCTIONS:**
        1. Start immediately with the **Aggressive Stance & Conviction** (e.g., "The Aggressive view strongly advocates for...").
        2. Seamlessly integrate **Speculative Drivers** (FOMO, squeeze potential) and **Contrarian Logic** into the narrative.
        3. Highlight the **Asymmetric Reward** (High Upside) naturally within the text.
        4. Conclude with the **Critical Trigger** or condition required for this high-risk play to pay off.
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
            return {"Summarize_aggressive_report": summary_content}
        except Exception as e:
            print(f"Error in summarizer: {e}")
            return {} # คืนค่าว่างถ้า error จะได้ไม่พัง
        
    return aggressive_node_summarizer
