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

        system_prompt = "You are a Senior Equity Research Analyst specializing in Fundamental Analysis. Your task is to synthesize financial data, key ratios, and market news into a concise, objective, and professional investment report. You must focus on four key pillars: Profitability, Financial Health, Growth, and Risks. Avoid generic statements; provide specific insights based on the data provided."
        
        user_prompt = f"""
        Analyze and summarize the fundamentals based on the following raw report:

        =========================================
        RAW DATA:
        {fundamental_report}
        =========================================

        Please generate a Final Fundamental Analysis Report using the following structure:

        1. **Executive Summary:**
           - A 2-3 sentence overview of the company's current financial standing (Bullish/Neutral/Bearish).

        2. **Key Strengths (Bull Case):**
           - List 3 specific strong points with data backing.

        3. **Key Risks (Bear Case):**
           - List 3 specific weak points or risks with data backing.

        4. **Future Outlook:**
           - A brief assessment of the business trajectory.

        5. **Final Verdict:**
           - A concise conclusion on the stock's fundamental attractiveness (e.g., Undervalued, Fairly Valued, Overvalued).
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
