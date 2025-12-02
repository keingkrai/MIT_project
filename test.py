import os
import json
import sys
from dotenv import load_dotenv
import sys

sys.stdout.reconfigure(encoding='utf-8')
print("\U0001f3c6 Trading Agents System Starting... \U0001f3c6")

load_dotenv()

try:
    from tradingagents.graph.trading_graph import TradingAgentsGraph
except ImportError as e:
    print(f"❌ Import Error: {e}")
    sys.exit(1)

# ---------------------------------------------------------
# 2. ฟังก์ชันช่วยแสดงผล (Helper Function)
# ---------------------------------------------------------
def print_section(title, content):
    print(f"\n{'='*15} {title} {'='*15}")
    if content:
        if isinstance(content, (dict, list)):
            print(json.dumps(content, indent=2, default=str, ensure_ascii=False))
        else:
            print(content)
    else:
        print("❌ No Data Available")

# ---------------------------------------------------------
# 3. เริ่มรันระบบ (Main Execution)
# ---------------------------------------------------------
def main():
    print("⚙️  Initializing System...")
    
    analysts = ["market", "social", "news", "fundamentals"]
    
    try:
        graph = TradingAgentsGraph(selected_analysts=analysts, debug=False)
        
        ticker = "AAPL"
        trade_date = "2025-11-30"

        print(f"🚀 Propagating for {ticker} on {trade_date}...")
        print("   (This process may take 1-3 minutes depending on your LLM speed)\n")
        
        final_state, final_decision = graph.propagate(company_name=ticker, trade_date=trade_date)

        print("✅ Execution Finished! Showing Results:\n")

        # ---------------------------------------------------------
        # 4. ดึงข้อมูลมาแสดง (Safe Access Mode)
        # ---------------------------------------------------------
             
        sum_finda = final_state.get("Summarize_fundamentals_report")
        funda = final_state.get("fundamentals_report")
        
        sum_market = final_state.get("Summarize_market_report")
        market = final_state.get("market_report")
        
        with open("./sum_funda.txt", 'w', encoding='utf-8') as f:
            f.write(str(sum_finda))
            
        with open("./full_funda.txt", 'w', encoding='utf-8') as f:
            f.write(str(funda))
            
        with open("./sum_market.txt", 'w', encoding='utf-8') as f:
            f.write(str(sum_market))
            
        with open("./full_market.txt", 'w', encoding='utf-8') as f:
            f.write(str(market))
        
        print_section("Long fundament", final_state.get("fundamentals_report"))
        print_section("Short fundament", final_state.get("Summarize_fundamentals_report"))
        
        
        
        # print_section("📊 Market Analyst Report", final_state.get("market_report"))

        # debate_state = final_state.get("investment_debate_state", {})
        # print_section("⚖️  Investment Judge Decision", debate_state.get("judge_decision"))

        # print_section("💰 Trader Plan", final_state.get("trader_investment_plan"))

        # risk_state = final_state.get("risk_debate_state", {})
        # print_section("🛡️  Risk Manager Decision", risk_state.get("judge_decision"))

        # print_section("🏁 Final Decision Signal", final_decision)

    except Exception as e:
        print(f"\n❌ An error occurred during execution:\n{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()