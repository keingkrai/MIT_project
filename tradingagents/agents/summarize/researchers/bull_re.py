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
            "You are a Senior Bullish Equity Researcher. Your goal is to synthesize "
            "the strongest arguments for BUYING the asset. Focus on growth catalysts, "
            "undervaluation, positive technical signals, and market opportunities. "
            "Be persuasive and optimistic but grounded in data."
        )

        user_prompt = f"""
        Synthesize the Bullish arguments from the debate history into a compelling summary:

        =========================================
        BULLISH ARGUMENTS LOG:
        {bull_researcher_report}
        =========================================

        **INSTRUCTIONS:**
        - Extract the most convincing reasons to buy.
        - Highlight any specific price targets or strong indicators mentioned.
        - Structure it as a "Long Thesis".

        **REQUIRED OUTPUT FORMAT:**

        ### 1.The Bull Case (Core Thesis)
        - **Main Driver:** The single biggest reason to buy right now (1-2 sentences).
        - **Conviction Level:** [High / Medium / Low]

        ### 2.Key Catalysts (Why Buy?)
        - **Fundamental:** (e.g., Strong earnings, Undervalued P/E).
        - **Technical:** (e.g., Breakout confirmed, RSI bullish).
        - **Macro/News:** (e.g., Fed rate cuts, Product launch).

        ### 3.Upside Potential
        - Describe the potential reward (e.g., "Potential for 20% upside due to...").

        ### 4.Analyst's Closing Statement
        - A punchy closing sentence advocating for a long position.
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
