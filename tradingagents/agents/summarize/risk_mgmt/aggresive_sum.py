import openai, os

# ควรสร้าง Client นอกฟังก์ชัน หรือใช้ Singleton เพื่อไม่ให้สร้าง connection ใหม่ทุกครั้งที่เรียก
client = openai.OpenAI(
    api_key=os.getenv("TYPHOON_API_KEY"),
    base_url="https://api.opentyphoon.ai/v1"
)

def create_summarizer_aggressive():
    def aggressive_node_summarizer(state) -> dict:

        # ดึงรายงานเดิมมา
        aggressive_report = state.get("risk_debate_state").get("risky_history")
        
        # ถ้าไม่มีรายงานเดิม ให้ข้ามไปเลย
        if not aggressive_report:
            return {} 

        system_prompt = """You are a Senior Risk & Aggressive-Stance Analyst.
Your job is to analyze high-risk debate logs, aggressive viewpoints, contrarian opinions, 
and bold speculative arguments, then convert them into a concise, actionable summary.

Your analysis must:
- Focus strictly on the information inside the provided risky debate history.
- Identify aggressive viewpoints, speculative reasoning, fear/greed elements, and risk-heavy assumptions.
- Highlight conflicts between aggressive and conservative perspectives.
- Avoid explaining what the metrics or concepts mean.
- Present insights clearly, analytically, and without emotional bias.

Goal: Produce a sharp, high-clarity summary of aggressive reasoning, highlighting risks, opportunities, 
and extreme viewpoints in a structured, decision-ready format."""
        user_prompt = f"""
Synthesize the following aggressive/contrarian debate content into a concise analytical summary:

=========================================
RAW RISK & AGGRESSIVE DEBATE HISTORY:
{aggressive_report}
=========================================

**INSTRUCTIONS:**
- Base your conclusions strictly on the risky, aggressive, or contrarian perspectives provided.
- Identify aggressive reasoning, bold assumptions, fear/greed behavior, and speculative logic.
- Highlight contradictions or internal conflicts within the arguments.
- Keep the summary structured, clean, and easy to scan.
- Do NOT add external assumptions.

**REQUIRED OUTPUT FORMAT:**

### 1. Aggressive Stance Overview
- **Direction:** [Strongly Bullish / Aggressive Bearish / Contrarian / Highly Speculative]
- **Confidence Level:** [High / Medium / Low]
- **Reasoning Summary:** Short rationale directly derived from the debate content.

### 2. Key Aggressive Arguments
- **High-Risk Claims:** (Statements based on bold/speculative logic)
- **Supporting Evidence:** (Data or narratives used to justify them)
- **Speculative Drivers:** (Greed signals, FOMO, panic reasoning, rapid-reversal expectations)

### 3. Critical Risk Observations
- **Conflicts or Logical Tensions:** (e.g., “Bullish conviction despite negative macro context”)
- **Fragile Assumptions:** (Things that could easily fail)
- **Potential Breaking Points:** (Conditions where aggressive stance collapses)

### 4. Actionable Aggressive Insight
- Provide 1–2 concise aggressive or contrarian insights 
  (e.g., “High-reward setup if X occurs,” “Watch for capitulation signal at Y,” “Momentum flip could ignite upside volatility.”)
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
            return {"Summarize_aggressive_report": summary_content}
        except Exception as e:
            print(f"Error in summarizer: {e}")
            return {} # คืนค่าว่างถ้า error จะได้ไม่พัง
        
    return aggressive_node_summarizer
