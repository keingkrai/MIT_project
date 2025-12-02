import openai, os

# ควรสร้าง Client นอกฟังก์ชัน หรือใช้ Singleton เพื่อไม่ให้สร้าง connection ใหม่ทุกครั้งที่เรียก
client = openai.OpenAI(
    api_key=os.getenv("TYPHOON_API_KEY"),
    base_url="https://api.opentyphoon.ai/v1"
)

def create_summarizer_conservative():
    def conservative_node_summarizer(state) -> dict:
        
        # ดึงรายงานเดิมมา
        conservative_report = state.get("risk_debate_state").get("safe_history")
        
        # ถ้าไม่มีรายงานเดิม ให้ข้ามไปเลย
        if not conservative_report:
            return {} 

        system_prompt = """You are a Senior Conservative-Risk Analyst.
Your role is to analyze safe, cautious, and risk-averse debate content and convert it into a concise, 
actionable summary.

Your analysis must:
- Focus strictly on the information inside the provided conservative debate history.
- Identify caution signals, risk-avoidance reasoning, stability-focused viewpoints, and concerns about uncertainty.
- Highlight conservative logic, risk minimization principles, and defensive arguments.
- Avoid explaining what metrics or concepts mean.
- Present insights clearly, carefully, and objectively.

Goal: Produce a clean, highly-structured conservative summary that highlights stable viewpoints,
risk-averse thinking, and protective strategies suitable for decision-making."""
        user_prompt = f"""
Synthesize the following conservative and risk-averse debate content into a concise analytical summary:

=========================================
RAW CONSERVATIVE DEBATE HISTORY:
{conservative_report}
=========================================

**INSTRUCTIONS:**
- Base your conclusions strictly on the cautious, conservative, or safety-focused arguments in the data.
- Identify warnings, uncertainties, concerns, risk-avoidance logic, and arguments favoring stability.
- Highlight contradictions or points where caution conflicts with optimism.
- Keep the summary structured, clean, and easy to scan.
- Do NOT add any external assumptions.

**REQUIRED OUTPUT FORMAT:**

### 1. Conservative Stance Overview
- **Position:** [Risk-Averse / Defensive / Cautiously Neutral / Seeking Stability]
- **Confidence Level:** [High / Medium / Low]
- **Reasoning Summary:** Short explanation derived directly from the debate content.

### 2. Key Conservative Arguments
- **Primary Concerns:** (Risks, uncertainties, threats, unclear signals)
- **Stability Factors:** (Elements supporting caution or defensive positioning)
- **Evidence Used:** (Any data or reasoning used to justify the conservative view)
- **Risk-Avoidance Principles:** (Focus on safety, capital preservation, uncertainty reduction)

### 3. Critical Observations
- **Conflicts or Caution Flags:** (e.g., “Positive short-term movement but high long-term uncertainty”)
- **Fragile Areas:** (Weak signals, limited confirmation, unclear trends)
- **Potential Downside Catalysts:** (Events that could increase risk)

### 4. Actionable Conservative Insight
- Provide 1–2 concise defensive or protective recommendations 
  (e.g., “Wait for clearer confirmation,” “Avoid aggressive positioning,” 
   “Monitor for downside catalysts before committing capital.”)
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
            return {"Summarize_conservative_report": summary_content}
        except Exception as e:
            print(f"Error in summarizer: {e}")
            return {} # คืนค่าว่างถ้า error จะได้ไม่พัง
        
    return conservative_node_summarizer