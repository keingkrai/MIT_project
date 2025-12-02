import openai, os

# ควรสร้าง Client นอกฟังก์ชัน หรือใช้ Singleton เพื่อไม่ให้สร้าง connection ใหม่ทุกครั้งที่เรียก
client = openai.OpenAI(
    api_key=os.getenv("TYPHOON_API_KEY"),
    base_url="https://api.opentyphoon.ai/v1"
)

def create_summarizer_trader():
    def trader_summarizer(state) -> dict:
        
        # ดึงรายงานเดิมมา
        trader_report = state.get("trader_investment_plan")
        
        # ถ้าไม่มีรายงานเดิม ให้ข้ามไปเลย
        if not trader_report:
            return {} 
        
        system_prompt = (
            "You are a Senior Execution Trader. Your goal is to formulate a clear, "
            "tactical trading plan based on the analysis provided. "
            "Focus on Price Levels (Entry, Stop Loss, Take Profit), "
            "Position Sizing logic, and the specific Strategy (Breakout, Reversal, Trend Following)."
        )

        user_prompt = f"""
        Synthesize the following Trading Plan into a concise execution setup:

        =========================================
        RAW TRADING PLAN:
        {trader_report}
        =========================================

        **INSTRUCTIONS:**
        - Extract the concrete numbers (Prices, %. allocation).
        - Identify the core strategy used.
        - Be tactical and precise.

        **REQUIRED OUTPUT FORMAT:**

        ### 1.Trade Setup (The Action)
        - **Strategy:** (e.g., "Trend Following Breakout", "Mean Reversion").
        - **Action:** [BUY / SELL / WAIT]
        - **Timeframe:** (e.g., Swing Trade, Long Term Investment).

        ### 2.Key Levels (The Numbers)
        - **Entry Zone:** [Price Range]
        - **Stop Loss:** [Price Level] (Crucial!)
        - **Target/Take Profit:** [Price Level]

        ### 3.Position Sizing
        - **Proposed Size:** (e.g., "5% of Portfolio", "Medium Conviction").
        - **Risk Rationale:** Why this size? (e.g., "High volatility warrants smaller size").

        ### 4.Trader's Note
        - A brief comment on execution timing (e.g., "Enter at market open", "Wait for close above $X").
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
            return {"trader_summarizer": summary_content}

        except Exception as e:
            print(f"Error in summarizer: {e}")
            return {} # คืนค่าว่างถ้า error จะได้ไม่พัง
        
    return trader_summarizer
