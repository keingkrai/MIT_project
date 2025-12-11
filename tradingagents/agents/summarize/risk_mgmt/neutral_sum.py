import openai, os

# ควรสร้าง Client นอกฟังก์ชัน หรือใช้ Singleton เพื่อไม่ให้สร้าง connection ใหม่ทุกครั้งที่เรียก
client = openai.OpenAI(
    api_key=os.getenv("TYPHOON_API_KEY"),
    base_url="https://api.opentyphoon.ai/v1"
)

def create_summarizer_neutral():
    def neutral_node_summarizer(state) -> dict:
        
        # ดึงรายงานเดิมมา
        neutral_report = state.get("risk_debate_state").get("neutral_history")
        
        # ถ้าไม่มีรายงานเดิม ให้ข้ามไปเลย
        if not neutral_report:
            return {} 

        system_prompt = """You are a Senior Neutral-Stance Analyst.
Your job is to interpret balanced, non-biased debate content and produce a concise, 
objective summary without leaning toward bullish or bearish extremes.

Your analysis must:
- Focus purely on the information in the provided neutral debate history.
- Identify balanced reasoning, evenly weighted arguments, and points of agreement or uncertainty.
- Highlight central themes, factual observations, and stable or indecisive areas.
- Avoid emotional tone, bias, or directional assumptions.
- Present all insights clearly, analytically, and with strict neutrality.

Goal: Produce a clean, structured neutral summary suitable for decision-making without bias or speculation."""

        user_prompt = f"""
Synthesize the following neutral, balanced debate content into a concise analytical summary:

=========================================
RAW NEUTRAL DEBATE HISTORY:
{neutral_report}
=========================================

**INSTRUCTIONS:**
- Base all conclusions strictly on the provided neutral discussion.
- Identify balanced viewpoints, areas of uncertainty, evenly weighted pros/cons, 
  and observations that do not strongly lean in any direction.
- Highlight points of agreement, unresolved questions, and mixed or ambiguous signals.
- Keep the summary structured, clean, and easy to scan.
- Do NOT add external assumptions or take sides.

**REQUIRED OUTPUT FORMAT:**

### 1. Neutral Overview
- **Stance:** [Balanced / Mixed / Indecisive / Observational]
- **Clarity Level:** [Clear / Partially Clear / Uncertain]
- **Reasoning Summary:** Short neutral explanation based only on the provided content.

### 2. Key Neutral Insights
- **Main Observations:** (Facts, signals, or narratives that appear consistent)
- **Balanced Points:** (Pros vs cons, mixed indicators, dual-sided arguments)
- **Uncertainties:** (Areas lacking clarity, inconsistent evidence, or ambiguous sentiment)
- **Consensus Areas:** (Topics the discussion broadly agrees on)

### 3. Critical Observations
- **Conflicts or Mixed Signals:** (e.g., “Some see upside potential while sentiment remains muted”)
- **Gaps in Information:** (Missing confirmation, unclear drivers)
- **Stability Factors:** (Elements indicating neutrality or low conviction)

### 4. Actionable Neutral Insight
- Provide 1–2 balanced, non-directional interpretations 
  (e.g., “Wait for clearer confirmation,” “Monitor both upside and downside catalysts,” 
   “Neutral stance appropriate until new data shifts conviction.”)
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
            return {"Summarize_neutral_report": summary_content}
        except Exception as e:
            print(f"Error in summarizer: {e}")
            return {} # คืนค่าว่างถ้า error จะได้ไม่พัง
        
    return neutral_node_summarizer
