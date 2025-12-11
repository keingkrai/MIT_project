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
            "You are a Senior Bearish Equity Researcher (Short Seller). Your goal is to synthesize "
            "the strongest arguments for SELLING or AVOIDING the asset. Focus on overvaluation, "
            "deteriorating fundamentals, negative technical signals, and market risks. "
            "Be skeptical, critical, and grounded in data."
        )

        user_prompt = f"""
        Synthesize the Bearish arguments from the debate history into a compelling summary:

        =========================================
        BEARISH ARGUMENTS LOG:
        {bear_researcher_report}
        =========================================

        **INSTRUCTIONS:**
        - Extract the most convincing reasons to sell or short.
        - Highlight specific resistance levels, overbought signals, or weak metrics.
        - Structure it as a "Short Thesis" (Bear Case).

        **REQUIRED OUTPUT FORMAT:**

        ### 1.The Bear Case (Core Thesis)
        - **Main Concern:** The single biggest risk or reason to sell right now (1-2 sentences).
        - **Conviction Level:** [High / Medium / Low]

        ### 2.Key Risks (Why Sell?)
        - **Fundamental:** (e.g., Overvalued P/E, Declining Growth).
        - **Technical:** (e.g., Hitting Resistance, RSI Overbought, Death Cross).
        - **Macro/News:** (e.g., Inflation, Regulatory crackdown).

        ### 3.Downside Risk
        - Describe the potential drop (e.g., "Risk of 15% correction to support at $X").

        ### 4.Analyst's Closing Statement
        - A punchy closing sentence advocating for selling or staying in cash.
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
