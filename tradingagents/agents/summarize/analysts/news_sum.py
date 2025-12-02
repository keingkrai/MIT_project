import openai, os

# ควรสร้าง Client นอกฟังก์ชัน หรือใช้ Singleton เพื่อไม่ให้สร้าง connection ใหม่ทุกครั้งที่เรียก
client = openai.OpenAI(
    api_key=os.getenv("TYPHOON_API_KEY"),
    base_url="https://api.opentyphoon.ai/v1"
)

def create_summarizer_news():
    def news_summarizer(state) -> dict:
        
        # ดึงรายงานเดิมมา
        news_report = state.get("news_report")
        
        # ถ้าไม่มีรายงานเดิม ให้ข้ามไปเลย
        if not news_report:
            return {} 

        system_prompt = """You are a Senior News Intelligence Analyst.
Your job is to review raw news data and convert it into a concise, actionable summary.

Your analysis should:
- Focus exclusively on the content of the provided news report.
- Identify sentiment, narrative direction, supportive or conflicting storylines, tone, and potential market-moving catalysts.
- Detect risks, opportunities, and notable shifts in coverage.
- Avoid explaining what news metrics or terms mean.
- Present insights clearly, professionally, and analytically.

Goal: Produce a clean, decision-ready news summary suitable for use in investment, strategic, or narrative analysis."""
        user_prompt = f"""
Synthesize the following news intelligence into a concise analytical summary:

=========================================
RAW NEWS REPORT:
{news_report}
=========================================

**INSTRUCTIONS:**
- Base every conclusion strictly on the provided news data.
- Identify sentiment, tone, key narratives, risks, opportunities, and catalysts.
- Highlight contradictions if they exist (e.g., “Positive earnings but warnings about slowing demand”).
- Keep the summary structured, objective, and easy to scan.
- Do NOT add external assumptions.

**REQUIRED OUTPUT FORMAT:**

### 1. Overall News Sentiment
- **Sentiment:** [Positive / Neutral / Negative / Mixed]
- **Trend:** [Improving / Declining / Stable]
- **Reasoning:** Brief explanation based only on the news content.

### 2. Key News Signals
- **Dominant Narratives:** (Main themes the articles emphasize)
- **Market or Sector Impact:** (If applicable)
- **Risk Factors:** (Warnings, regulatory concerns, geopolitical notes)
- **Opportunities / Positive Drivers:** (Strong earnings, innovation, expansions)
- **Credible Sources Influencing Tone:** (If mentioned in report)

### 3. Critical Observations
- **Conflicts or Mixed Signals:** (e.g., “Strong revenue but poor forward guidance”)
- **Potential Catalysts:** (Events or developments that might shift sentiment or markets)

### 4. Actionable Insight
- Provide 1–2 concise insights useful for strategic or investment decisions
  (e.g., “Monitor regulatory developments,” “Sentiment likely to turn bearish if X worsens”).
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
            return {"Summarize_news_report": summary_content}
        except Exception as e:
            print(f"Error in summarizer: {e}")
            return {} # คืนค่าว่างถ้า error จะได้ไม่พัง
        
    return news_summarizer
