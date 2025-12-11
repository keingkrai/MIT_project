import openai, os

# ควรสร้าง Client นอกฟังก์ชัน หรือใช้ Singleton เพื่อไม่ให้สร้าง connection ใหม่ทุกครั้งที่เรียก
client = openai.OpenAI(
    api_key=os.getenv("TYPHOON_API_KEY"),
    base_url="https://api.opentyphoon.ai/v1"
)

def create_summarizer_social():
    def social_node_summarizer(state) -> dict:
        
        # ดึงรายงานเดิมมา
        social_report = state.get("sentiment_report")
        
        # ถ้าไม่มีรายงานเดิม ให้ข้ามไปเลย
        if not social_report:
            return {} 

        system_prompt = """You are a Senior Social Media Intelligence Analyst. 
Your role is to interpret raw social media insights and convert them into a concise, actionable summary.

Your analysis should:
- Focus strictly on information derived from the provided social media report.
- Identify sentiment direction, public mood, conversation trends, volume patterns, and potential catalysts.
- Highlight conflicts (e.g., rising volume but declining sentiment).
- Avoid explaining what social media metrics are.
- Present insights clearly, analytically, and professionally.

Your goal: Produce a clean, decision-ready summary that can be used in broader market or narrative analysis."""
        
        user_prompt = f"""
Synthesize the following social media intelligence into a concise analytical summary:

=========================================
RAW SOCIAL MEDIA REPORT:
{social_report}
=========================================

**INSTRUCTIONS:**
- Base every conclusion strictly on the provided social media data.
- Identify sentiment trends, shifts, anomalies, and traction levels.
- Highlight contradictions if they exist (e.g., “Sentiment is negative but engagement is rising sharply”).
- Keep the summary short, structured, and easy to scan.
- Do NOT add external assumptions.

**REQUIRED OUTPUT FORMAT:**

### 1. Overall Social Sentiment
- **Sentiment:** [Positive / Neutral / Negative / Mixed]
- **Trend:** [Improving / Declining / Stable]
- **Reasoning:** Clear explanation based only on the data.

### 2. Key Social Signals
- **Buzz & Volume:** (Conversation growth, spikes, sudden drops)
- **Dominant Narratives:** (Main topics the crowd is focused on)
- **Audience Mood:** (Emotional tone, concerns, excitement)
- **Influencer / Media Impact:** (If present in raw data)

### 3. Critical Observations
- **Conflicts or Anomalies:** (e.g., “High volume but sentiment collapse”)
- **Potential Catalysts:** (Events or themes driving discussions)

### 4. Actionable Insight
- Provide 1–2 concise actions or interpretations useful for broader decision-making 
  (e.g., “Monitor sentiment reversal,” “Track narrative around X,” “Expect heightened volatility in discussions.”)
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
            return {"Summarize_social_report": summary_content}
        except Exception as e:
            print(f"Error in summarizer: {e}")
            return {} # คืนค่าว่างถ้า error จะได้ไม่พัง
        
    return social_node_summarizer
