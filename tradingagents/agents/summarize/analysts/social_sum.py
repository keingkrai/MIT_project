import openai, os

# ควรสร้าง Client นอกฟังก์ชัน หรือใช้ Singleton เพื่อไม่ให้สร้าง connection ใหม่ทุกครั้งที่เรียก
client = openai.OpenAI(
    api_key=os.getenv("TYPHOON_API_KEY"),
    base_url="https://api.opentyphoon.ai/v1"
)

def create_summarizer_social():
    def social_node_summarizer(state) -> dict:
        
        # ดึงรายงานเดิมมา
        social_report = state.get("sentiment_report")
        
        # ถ้าไม่มีรายงานเดิม ให้ข้ามไปเลย
        if not social_report:
            return {} 

        system_prompt = (
            "You are a Senior Social Media Intelligence Analyst. "
            "Your task is to distill raw social sentiment data into a **single, high-density executive summary**. "
            "Do NOT use section headers, bullet points, or lists. "
            "Write in a professional, narrative paragraph format. "
            "Focus on crowd psychology, volume anomalies, and contrarian signals."
        )
        
        user_prompt = f"""
        Synthesize the social media intelligence below into a concise summary (max 150 words).

        =========================================
        RAW SOCIAL MEDIA REPORT:
        {social_report}
        =========================================

        **INSTRUCTIONS:**
        1. Start immediately with the **Overall Crowd Sentiment** (e.g., "Retail sentiment has shifted to Extreme Greed due to...").
        2. Seamlessly integrate **Volume/Buzz trends** (spikes, silence) and the **Dominant Narrative** driving the discussion.
        3. Highlight any **Psychological Extremes** (FOMO, Panic, Capitulation) naturally within the text.
        4. Conclude with a **Contrarian or Volatility Insight** (e.g., "High volume suggests a potential top").
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
            return {"Summarize_social_report": summary_content}
        except Exception as e:
            print(f"Error in summarizer: {e}")
            return {} # คืนค่าว่างถ้า error จะได้ไม่พัง
        
    return social_node_summarizer
