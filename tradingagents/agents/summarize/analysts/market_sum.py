import openai, os

# ควรสร้าง Client นอกฟังก์ชัน หรือใช้ Singleton เพื่อไม่ให้สร้าง connection ใหม่ทุกครั้งที่เรียก
client = openai.OpenAI(
    api_key=os.getenv("TYPHOON_API_KEY"),
    base_url="https://api.opentyphoon.ai/v1"
)

def create_summarizer_market():
    def market_node_summarizer(state) -> dict:
        
        # ดึงรายงานเดิมมา
        market_report = state.get("market_report")
        
        # ถ้าไม่มีรายงานเดิม ให้ข้ามไปเลย
        if not market_report:
            return {} 

        system_prompt = (
            "You are an expert Technical Analyst. "
            "Your goal is to compress complex chart data (Price Action, Indicators, Levels) "
            "into a **single, high-impact trading narrative**. "
            "Do NOT use bullet points, lists, or section headers. "
            "Write in a dense, professional paragraph."
        )
        
        user_prompt = f"""
        Synthesize the raw technical data below into a concise summary (max 150 words).

        =========================================
        RAW DATA INPUT:
        {market_report}
        =========================================

        **INSTRUCTIONS:**
        1. Start the paragraph immediately with the **Technical Verdict** (e.g., "Technically Bullish", "Neutral with Bearish bias").
        2. Seamlessly weave in the **Momentum** and **Volume** context to support your verdict.
        3. Mention the critical **Support and Resistance levels** naturally within the sentences (do not list them).
        4. Conclude with the immediate **Actionable Setup** (e.g., "Wait for a pullback to [Price] before entering").
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
            return {"Summarize_market_report": summary_content}

        except Exception as e:
            print(f"Error in summarizer: {e}")
            return {} # คืนค่าว่างถ้า error จะได้ไม่พัง
        
    return market_node_summarizer
