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

        system_prompt = """You are a Lead Technical Analyst. Your task is to interpret raw technical data "
            "(Price Action, Moving Averages, RSI, MACD, Volume) and convert it into a "
            "decisive trading stance. Do not explain what an indicator is. "
            "Focus purely on what the data implies for future price movement."""
        
        user_prompt = f"""
        Synthesize the following technical analysis into a concise summary:

        =========================================
        RAW DATA INPUT:
        {market_report}
        =========================================

        **INSTRUCTIONS:**
        - Base every conclusion strictly on the provided data.
        - If indicators conflict, state the conflict clearly (e.g., "Trend is Bullish but Momentum is slowing").
        - Keep it short, bullet-pointed, and easy to scan.

        **REQUIRED OUTPUT FORMAT:**

        ### 1.The Verdict (Trend Analysis)
        - **Direction:** [Bullish / Bearish / Sideways]
        - **Strength:** [Strong / Weak / Consolidating]
        - **Reasoning:** (e.g., "Price holds above 200 SMA," "Golden Cross confirmed")

        ### 2.Key Signals (Data Interpretation)
        - **Momentum:** (Interpret RSI/MACD: e.g., "RSI at 75 indicates overbought conditions.")
        - **Volatility:** (Interpret Bollinger Bands/ATR: e.g., "Bands squeezing suggests imminent breakout.")
        - **Volume:** (Confirming the move or diverging?)

        ### 3.Critical Zones
        - **Immediate Support:** [Price Level]
        - **Immediate Resistance:** [Price Level]

        ### 4.Actionable Setup
        - Suggest a potential setup based **only** on the data (e.g., "Look for breakout above X," "Wait for pullback to Y").
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
