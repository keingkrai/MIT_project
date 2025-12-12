import openai, os

# ควรสร้าง Client นอกฟังก์ชัน หรือใช้ Singleton เพื่อไม่ให้สร้าง connection ใหม่ทุกครั้งที่เรียก
client = openai.OpenAI(
    api_key=os.getenv("TYPHOON_API_KEY"),
    base_url="https://api.opentyphoon.ai/v1"
)

def create_summarizer_bull_researcher():
    def bull_researcher_summarizer(state) -> dict:
        
        # ดึงรายงานเดิมมา
        debate = state.get("investment_debate_state")
        bull_researcher_report = debate.get("bull_history")
        
        # ถ้าไม่มีรายงานเดิม ให้ข้ามไปเลย
        if not bull_researcher_report:
            return {} 
        
        system_prompt = (
            "You are a Senior Bullish Equity Researcher. "
            "Your task is to synthesize the bullish arguments into a **single, high-density executive summary**. "
            "Do NOT use section headers, bullet points, or lists. "
            "Write in a professional, persuasive, and narrative paragraph format. "
            "Focus on growth catalysts, undervaluation, and upside potential."
        )

        user_prompt = f"""
        Synthesize the Bullish arguments below into a concise summary (max 150 words).

        =========================================
        BULLISH ARGUMENTS LOG:
        {bull_researcher_report}
        =========================================

        **INSTRUCTIONS:**
        1. Start immediately with the **Core Long Thesis** (e.g., "The asset presents a compelling buy opportunity due to...").
        2. Seamlessly integrate **Fundamental Strengths** (earnings, growth) and **Technical Breakouts** into the narrative.
        3. Highlight the specific **Upside Potential** (price target or expected return) naturally within the sentences.
        4. Maintain an optimistic and conviction-driven tone throughout.
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
            return {"bull_researcher_summarizer": summary_content}

        except Exception as e:
            print(f"Error in summarizer: {e}")
            return {} # คืนค่าว่างถ้า error จะได้ไม่พัง
        
    return bull_researcher_summarizer
