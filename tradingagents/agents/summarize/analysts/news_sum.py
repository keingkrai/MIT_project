import openai, os

# ควรสร้าง Client นอกฟังก์ชัน หรือใช้ Singleton เพื่อไม่ให้สร้าง connection ใหม่ทุกครั้งที่เรียก
client = openai.OpenAI(
    api_key=os.getenv("TYPHOON_API_KEY"),
    base_url="https://api.opentyphoon.ai/v1"
)

def create_summarizer_news():
    def news_summarizer(state) -> dict:
        
        # ดึงรายงานเดิมมา
        news_report = state.get("news_report")
        
        # ถ้าไม่มีรายงานเดิม ให้ข้ามไปเลย
        if not news_report:
            return {} 

        system_prompt = (
            "You are a Senior News Intelligence Analyst. "
            "Your task is to synthesize raw news reports into a **single, high-density executive summary**. "
            "Do NOT use section headers, bullet points, or lists. "
            "Write in a professional, narrative paragraph format. "
            "Focus on the dominant sentiment, key catalysts, and critical risks."
        )
        
        user_prompt = f"""
        Synthesize the news intelligence below into a concise summary (max 150 words).

        =========================================
        RAW NEWS REPORT:
        {news_report}
        =========================================

        **INSTRUCTIONS:**
        1. Start immediately with the **Overall News Sentiment** (e.g., "News sentiment is currently Negative due to...").
        2. Seamlessly integrate the **Dominant Narratives** and **Key Drivers** (earnings, regulations, etc.) into the text.
        3. Mention any critical **Risks or Conflicts** naturally within the sentences.
        4. Conclude with the primary **Implication** for the stock/market (e.g., "Expect volatility ahead of the ruling").
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
            return {"Summarize_news_report": summary_content}
        except Exception as e:
            print(f"Error in summarizer: {e}")
            return {} # คืนค่าว่างถ้า error จะได้ไม่พัง
        
    return news_summarizer
