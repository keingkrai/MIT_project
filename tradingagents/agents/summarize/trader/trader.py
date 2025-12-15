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
            "You are a Senior Execution Trader. "
            "Your task is to synthesize the Trading Plan into a **single, high-density execution summary**. "
            "Do NOT use section headers, bullet points, or lists. "
            "Write in a precise, tactical, and narrative paragraph format. "
            "Focus strictly on the Action, Exact Price Levels, and Position Sizing."
        )

        user_prompt = f"""
        Synthesize the trading plan below into a concise summary (max 150 words).

        =========================================
        RAW TRADING PLAN:
        {trader_report}
        =========================================

        **INSTRUCTIONS:**
        1. Start immediately with the **Primary Action & Strategy** (e.g., "Execute a Breakout Long on [Symbol]...").
        2. Seamlessly embed the **Exact Key Levels** (Entry Zone, Hard Stop Loss, Take Profit) into the narrative.
        3. Specify the **Position Size & Risk Rationale** clearly within the text.
        4. Conclude with the **Execution Trigger** (e.g., "Enter only upon market open").
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
