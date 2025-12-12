import openai, os

# ควรสร้าง Client นอกฟังก์ชัน หรือใช้ Singleton เพื่อไม่ให้สร้าง connection ใหม่ทุกครั้งที่เรียก
client = openai.OpenAI(
    api_key=os.getenv("TYPHOON_API_KEY"),
    base_url="https://api.opentyphoon.ai/v1"
)

def create_summarizer_fundamental():
    def fundamental_node_summarizer(state) -> dict:
        
        # ดึงรายงานเดิมมา
        fundamental_report = state.get("fundamentals_report")
        
        # ถ้าไม่มีรายงานเดิม ให้ข้ามไปเลย
        if not fundamental_report:
            return {} 

        system_prompt = (
                    "You are a Senior Equity Research Analyst. "
                    "Your task is to synthesize financial data into a **single, high-density executive summary**. "
                    "Do NOT use section headers, bullet points, or lists. "
                    "Write in a professional, narrative paragraph format. "
                    "Focus only on the most critical insights: Valuation, Financial Health, and Key Risks."
                )        
        user_prompt = f"""
        Analyze the raw data below and write a concise summary (max 150 words).

        =========================================
        RAW DATA:
        {fundamental_report}
        =========================================

        **INSTRUCTIONS:**
        1. Start the paragraph immediately with the fundamental verdict (e.g., "The stock is currently Undervalued due to...").
        2. Seamlessly integrate the key strengths (growth/profitability) and the single biggest risk into the narrative.
        3. Use specific numbers to back up your claims, but keep the flow natural.
        4. No fluff, no intro/outro filler. Just the analysis.
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
            return {"Summarize_fundamentals_report": summary_content}

        except Exception as e:
            print(f"Error in summarizer: {e}")
            return {} # คืนค่าว่างถ้า error จะได้ไม่พัง
        
    return fundamental_node_summarizer
