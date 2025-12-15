import openai, os

# ควรสร้าง Client นอกฟังก์ชัน หรือใช้ Singleton เพื่อไม่ให้สร้าง connection ใหม่ทุกครั้งที่เรียก
client = openai.OpenAI(
    api_key=os.getenv("TYPHOON_API_KEY"),
    base_url="https://api.opentyphoon.ai/v1"
)

def create_summarizer_bear_researcher():
    def bear_researcher_summarizer(state) -> dict:
        
        # ดึงรายงานเดิมมา
        debate = state.get("investment_debate_state")
        bear_researcher_report = debate.get("bear_history")
        
        # ถ้าไม่มีรายงานเดิม ให้ข้ามไปเลย
        if not bear_researcher_report:
            return {} 
        
        system_prompt = (
            "You are a Senior Bearish Equity Researcher (Short Seller). "
            "Your task is to synthesize the bearish arguments into a **single, high-density executive summary**. "
            "Do NOT use section headers, bullet points, or lists. "
            "Write in a professional, critical, and narrative paragraph format. "
            "Focus on overvaluation, technical breakdown signals, and downside targets."
        )

        user_prompt = f"""
        Synthesize the Bearish arguments below into a concise summary (max 150 words).

        =========================================
        BEARISH ARGUMENTS LOG:
        {bear_researcher_report}
        =========================================

        **INSTRUCTIONS:**
        1. Start immediately with the **Core Short Thesis** (e.g., "The asset is critically overvalued due to...").
        2. Seamlessly integrate **Fundamental Flaws** (weak earnings, debt) and **Technical Warnings** (resistance, divergence).
        3. Highlight the specific **Downside Risk** (price target or % drop) naturally within the sentences.
        4. Maintain a skeptical and cautionary tone throughout.
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
            return {"bear_researcher_summarizer": summary_content}

        except Exception as e:
            print(f"Error in summarizer: {e}")
            return {} # คืนค่าว่างถ้า error จะได้ไม่พัง
        
    return bear_researcher_summarizer
