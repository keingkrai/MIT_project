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
    # analysts = ["market"]
    
    try:
        graph = TradingAgentsGraph(selected_analysts=analysts, debug=False)
        
        ticker = "NVDA"
        trade_date = "2025-11-30"

        print(f"🚀 Propagating for {ticker} on {trade_date}...")
        print("   (This process may take 1-3 minutes depending on your LLM speed)\n")
        
        final_state, final_decision = graph.propagate(company_name=ticker, trade_date=trade_date)
        with open("./final_state.txt", 'w', encoding='utf-8') as f:
            f.write(str(final_state))

        print("✅ Execution Finished! Showing Results:\n")

        # ---------------------------------------------------------
        # 4. ดึงข้อมูลมาแสดง (Safe Access Mode)
        # ---------------------------------------------------------
             
        # sum_market = final_state.get("Summarize_market_report")
        # market = final_state.get("market_report")

        # sum_cial = final_state.get("Summarize_social_report")
        # social = final_state.get("sentiment_report")

        # sum_news = final_state.get("Summarize_news_report")
        # news = final_state.get("news_report")

        # sum_finda = final_state.get("Summarize_fundamentals_report")
        # funda = final_state.get("fundamentals_report")

        
        # with open("./sum_funda.txt", 'w', encoding='utf-8') as f:
        #     f.write(str(sum_finda))
            
        # funda = json.loads(funda)
        # with open("./full_funda.json", 'w', encoding='utf-8') as f:
        #     json.dump(funda, f, ensure_ascii=False, indent=4)
            
        # with open("./sum_market.txt", 'w', encoding='utf-8') as f:
        #     f.write(str(sum_market))
            
        # market = json.loads(market)
        # with open("./full_market.json", 'w', encoding='utf-8') as f:
        #     json.dump(market, f, ensure_ascii=False, indent=4)

        # with open("./sum_social.txt", 'w', encoding='utf-8') as f:
        #     f.write(str(sum_cial))

        # social = json.loads(social)
        # with open("./full_social.json", 'w', encoding='utf-8') as f:
        #     json.dump(social, f, ensure_ascii=False, indent=4)

        # with open("./sum_news.txt", 'w', encoding='utf-8') as f:
        #     f.write(str(sum_news))
        
        # news = json.loads(news)
        # with open("./full_news.json", 'w', encoding='utf-8') as f:
        #     json.dump(news, f, ensure_ascii=False, indent=4)
        
        # sum_bull = final_state.get("bull_researcher_summarizer")
        # bull = final_state.get("investment_debate_state")
        
        # sum_bear = final_state.get("bear_researcher_summarizer")
        # bear = final_state.get("investment_debate_state")

        # with open("./sum_bull.txt", 'w', encoding='utf-8') as f:
        #     f.write(str(sum_bull))
            
        # # bull = json.loads(bull)
        # with open("./full_bull.json", 'w', encoding='utf-8') as f:
        #     json.dump(bull, f, ensure_ascii=False, indent=4)
            
        # with open("./sum_bear.txt", 'w', encoding='utf-8') as f:
        #     f.write(str(sum_bear))
        
        # # bear = json.loads(bear)
        # with open("./full_bear.json", 'w', encoding='utf-8') as f:
        #     json.dump(bear, f, ensure_ascii=False, indent=4)

        
        # sum_cons = final_state.get("Summarize_conservative_report")
        # cons = final_state.get("risk_debate_state")

        # sum_aggr = final_state.get("Summarize_aggressive_report")
        # aggr = final_state.get("risk_debate_state")

        # sum_neut = final_state.get("Summarize_neutral_report")
        # neut = final_state.get("risk_debate_state")

        # with open("./sum_conservative.txt", 'w', encoding='utf-8') as f:
        #     f.write(str(sum_cons))
        
        # # cons = json.loads(cons)
        # with open("./full_conservative.json", 'w', encoding='utf-8') as f:
        #     json.dump(cons, f, ensure_ascii=False, indent=4)

        # with open("./sum_aggressive.txt", 'w', encoding='utf-8') as f:
        #     f.write(str(sum_aggr))

        # # aggr = json.loads(aggr)
        # with open("./full_aggressive.json", 'w', encoding='utf-8') as f:
        #     json.dump(aggr, f, ensure_ascii=False, indent=4)

        # with open("./sum_neutral.txt", 'w', encoding='utf-8') as f:
        #     f.write(str(sum_neut))
        
        # # neut = json.loads(neut)
        # with open("./full_neutral.json", 'w', encoding='utf-8') as f:
        #     json.dump(neut, f, ensure_ascii=False, indent=4)
       
        # trader = final_state.get("trader_investment_plan")
        # sum_trader = final_state.get("trader_summarizer")

        # with open("./sum_trader.txt", 'w', encoding='utf-8') as f:
        #     f.write(str(sum_trader))
        
        # trader = json.loads(trader)
        # with open("./full_trader.json", 'w', encoding='utf-8') as f:
        #     json.dump(trader, f, ensure_ascii=False, indent=4)

        # investment_plan = final_state.get("investment_plan")
        # sum_investment_plan = final_state.get("Summarize_investment_plan_report")

        # final_decision = final_state.get("final_trade_decision")
        # sum_final_decision = final_state.get("Summarize_final_trade_decision_report")

        # with open("./investment_plan.txt", "w", encoding="utf-8") as f:
        #     f.write(str(investment_plan))

        # with open("./sum_investment_plan.txt", "w", encoding="utf-8") as f:
        #     f.write(str(sum_investment_plan))

        # with open("./final_decision.txt", "w", encoding="utf-8") as f:
        #     f.write(str(final_decision))

        # with open("./sum_final_decision.txt", "w", encoding="utf-8") as f:
        #     f.write(str(sum_final_decision))
  

    except Exception as e:
        print(f"\n❌ An error occurred during execution:\n{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()