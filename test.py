import os
import json
import sys

# ---------------------------------------------------------
# 1. ✅ แก้ปัญหา OpenAI Key Error (ต้องใส่ก่อนเรียก Graph)
# ---------------------------------------------------------
# ถ้าใช้ Local LLM (Ollama/LM Studio) ให้ใส่ Key อะไรก็ได้
# ถ้าใช้ OpenAI จริง ให้ใส่ Key จริงของคุณแทน
if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = "AIzaSyAqJrVRc6fSJGEQi20mEVNFhtZ0sATX5Lk"

# Import Graph (ต้องทำหลังจากตั้ง Env Var แล้ว)
try:
    from tradingagents.graph.trading_graph import TradingAgentsGraph
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("ตรวจสอบว่าคุณรันคำสั่งนี้ที่ Root Directory ของโปรเจกต์ (C:\\MIT_project)")
    sys.exit(1)

# ---------------------------------------------------------
# 2. ฟังก์ชันช่วยแสดงผล (Helper Function)
# ---------------------------------------------------------
def print_section(title, content):
    print(f"\n{'='*15} {title} {'='*15}")
    if content:
        if isinstance(content, (dict, list)):
            # จัดรูปแบบ JSON ให้อ่านง่าย
            print(json.dumps(content, indent=2, default=str, ensure_ascii=False))
        else:
            # แสดงข้อความธรรมดา
            print(content)
    else:
        print("❌ No Data Available")

# ---------------------------------------------------------
# 3. เริ่มรันระบบ (Main Execution)
# ---------------------------------------------------------
def main():
    print("⚙️  Initializing System...")
    
    # ตั้งค่าว่าจะใช้ Analyst คนไหนบ้าง
    analysts = ["market", "social", "news", "fundamentals"]
    
    try:
        # สร้าง Graph
        graph = TradingAgentsGraph(selected_analysts=analysts, debug=False)
        
        ticker = "AAPL"
        trade_date = "2025-11-27"

        print(f"🚀 Propagating for {ticker} on {trade_date}...")
        print("   (This process may take 1-3 minutes depending on your LLM speed)\n")
        
        # รัน propagate
        final_state, final_decision = graph.propagate(company_name=ticker, trade_date=trade_date)

        print("✅ Execution Finished! Showing Results:\n")

        # ---------------------------------------------------------
        # 4. ดึงข้อมูลมาแสดง (Safe Access Mode)
        # ---------------------------------------------------------
        
        # 1. Market Analysis
        print_section("📊 Market Analyst Report", final_state.get("market_report"))

        # 2. Debate Decision (ใช้ .get() ซ้อนกันกันพัง)
        debate_state = final_state.get("investment_debate_state", {})
        print_section("⚖️  Investment Judge Decision", debate_state.get("judge_decision"))

        # 3. Trader Plan
        print_section("💰 Trader Plan", final_state.get("trader_investment_plan"))

        # 4. Risk Decision
        risk_state = final_state.get("risk_debate_state", {})
        print_section("🛡️  Risk Manager Decision", risk_state.get("judge_decision"))

        # 5. Final Output
        print_section("🏁 Final Decision Signal", final_decision)

    except Exception as e:
        print(f"\n❌ An error occurred during execution:\n{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()