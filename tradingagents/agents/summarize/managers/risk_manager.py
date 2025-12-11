import openai, os

# ควรสร้าง Client นอกฟังก์ชัน หรือใช้ Singleton เพื่อไม่ให้สร้าง connection ใหม่ทุกครั้งที่เรียก
client = openai.OpenAI(
    api_key=os.getenv("TYPHOON_API_KEY"),
    base_url="https://api.opentyphoon.ai/v1"
)

def create_summarizer_risk_manager():
    def risk_manager_summarizer(state) -> dict:
        
        # ดึงรายงานเดิมมา
        final_trade_decision_report = state.get("final_trade_decision")
        
        # ถ้าไม่มีรายงานเดิม ให้ข้ามไปเลย
        if not final_trade_decision_report:
            return {} 

        system_prompt = """You are a Senior Risk Manager specializing in trade evaluation.
Your responsibility is to interpret the final trade decision report and produce a
clear, concise summary focused on risk, justification, and execution readiness.

Your analysis must:
- Base all conclusions strictly on the provided final trade decision report.
- Identify the trade rationale, risk exposure, conviction level, and execution logic.
- Highlight conflicts, uncertainties, and any red flags within the decision.
- Avoid adding external assumptions beyond the provided information.
- Present insights in a professional, structured format for decision approval."""

        user_prompt = f"""
Summarize the following final trade decision into a structured, risk-focused report:

=========================================
RAW FINAL TRADE DECISION REPORT:
{final_trade_decision_report}
=========================================

**INSTRUCTIONS:**
- Derive every conclusion strictly from the provided content.
- Identify the trade's direction, reasoning, expected outcomes, and risk considerations.
- Highlight inconsistencies or concerns, if present.
- Keep the summary clean, clear, and easy to evaluate.
- Do NOT add outside data or market knowledge.

**REQUIRED OUTPUT FORMAT:**

### 1. Trade Conclusion
- **Decision:** (Buy / Sell / Hold / No Trade)
- **Direction & Conviction:** (High / Medium / Low)
- **Core Reasoning:** Clear justification based only on the report.

### 2. Risk Assessment
- **Primary Risks:** (Downside scenarios, uncertainties, conflicting signals)
- **Risk Level:** [High / Medium / Low]
- **Risk Mitigation:** (Stops, hedges, position sizing logic)

### 3. Opportunity & Reward Logic
- **Upside Thesis:** (What supports the trade’s profitability?)
- **Key Conditions:** (Signals or triggers needed for success)

### 4. Critical Observations
- **Conflicts or Red Flags:** (e.g., strong signal but weak conviction)
- **Dependencies:** (Market conditions, catalysts mentioned in the report)

### 5. Actionable Recommendation
Provide 1–2 concise, risk-aware recommendations
(e.g., “Proceed with reduced position size,” “Wait for confirmation,” 
“Manage with tighter stop placement.”)
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
            return {"Summarize_final_trade_decision_report": summary_content}
        except Exception as e:
            print(f"Error in summarizer: {e}")
            return {} # คืนค่าว่างถ้า error จะได้ไม่พัง
        
    return risk_manager_summarizer
