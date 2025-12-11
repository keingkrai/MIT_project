"""
FastAPI backend for TradingAgents web interface.
Provides WebSocket support for real-time updates.
"""
import asyncio
import json
import datetime
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import requests
from rich import _console
from tradingagents.agents import *

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

try:
    from tradingagents.graph.trading_graph import TradingAgentsGraph
    from tradingagents.default_config import DEFAULT_CONFIG
    from cli.models import AnalystType
    logger.info("Successfully imported TradingAgents modules")
except ImportError as e:
    logger.error(f"Failed to import TradingAgents modules: {e}")
    raise

# Get the project root directory (parent of api directory)
PROJECT_ROOT = Path(__file__).parent.parent
WEB_DIR = PROJECT_ROOT / "web"

logger.info(f"Project root: {PROJECT_ROOT}")
logger.info(f"Web directory: {WEB_DIR} (exists: {WEB_DIR.exists()})")
WEB_DIST_DIR = WEB_DIR / "dist"
if WEB_DIST_DIR.exists():
    logger.info(f"Production build found: {WEB_DIST_DIR}")
else:
    logger.info(f"Using development web directory: {WEB_DIR}")

# Active WebSocket connections
active_connections: List[WebSocket] = []


class AnalysisRequest(BaseModel):
    """Request model for starting an analysis."""
    ticker: str
    analysis_date: str
    analysts: List[str]  # List of analyst types: ["market", "social", "news", "fundamentals"]
    research_depth: int  # 1, 3, or 5
    llm_provider: str  # "openai", "anthropic", "deepseek", etc.
    backend_url: str
    shallow_thinker: str
    deep_thinker: str
    report_length: str = "long"  # "short" or "long"


def extract_content_string(content):
    """Extract string content from various message formats."""
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get('type') == 'text':
                    text_parts.append(item.get('text', ''))
                elif item.get('type') == 'tool_use':
                    text_parts.append(f"[Tool: {item.get('name', 'unknown')}]")
            else:
                text_parts.append(str(item))
        return ' '.join(text_parts)
    else:
        return str(content)
    
def sent_to_telegram(message: str):
    """Send a message to Telegram if configured."""
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown",
        }
        try:
            response = requests.post(url, data=payload, timeout=10)
            response.raise_for_status()
            _console.print("[green]Report sent to Telegram successfully![/green]")
        except requests.RequestException as e:
            _console.print(f"[red]Failed to send report to Telegram: {e}[/red]")
    else:
        _console.print("[yellow]Telegram not configured. Skipping sending report.[/yellow]")




async def send_update(websocket: WebSocket, update_type: str, data: Dict[str, Any]):
    """Send an update to the WebSocket client."""
    try:
        await websocket.send_json({
            "type": update_type,
            "data": data,
            "timestamp": datetime.datetime.now().isoformat()
        })
    except Exception as e:
        print(f"Error sending update: {e}")


async def run_analysis_stream(websocket: WebSocket, request: AnalysisRequest):
    """Run the trading analysis and stream updates via WebSocket."""
    try:
        # Create config
        config = DEFAULT_CONFIG.copy()
        config["max_debate_rounds"] = request.research_depth
        config["max_risk_discuss_rounds"] = request.research_depth
        
        # Hardcoded to use DeepSeek AI - override any frontend requests
        config["quick_think_llm"] = "deepseek-chat"  # Hardcoded DeepSeek Chat
        config["deep_think_llm"] = "deepseek-reasoner"  # Hardcoded DeepSeek Reasoner
        config["backend_url"] = "https://api.deepseek.com/v1"  # Hardcoded DeepSeek API endpoint
        config["llm_provider"] = "deepseek"  # Hardcoded DeepSeek provider
        
        # Log the models being used
        logger.info(f"Using models - Quick: {config['quick_think_llm']}, Deep: {config['deep_think_llm']}")

        # Validate analysts list before using
        if request.analysts is None:
            await send_update(websocket, "error", {"message": "Analysts list cannot be None"})
            return
        
        if not isinstance(request.analysts, list) or len(request.analysts) == 0:
            await send_update(websocket, "error", {"message": "Analysts must be a non-empty list"})
            return

        # Initialize the graph
        graph = TradingAgentsGraph(
            request.analysts,
            config=config,
            debug=True
        )

        # Create result directory
        results_base = Path(config.get("results_dir", "./results"))
        if not results_base.is_absolute():
            # Make it relative to project root
            results_base = PROJECT_ROOT / results_base
        results_dir = results_base / request.ticker / request.analysis_date
        results_dir.mkdir(parents=True, exist_ok=True)
        report_dir = results_dir / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)

        # Initialize state
        init_agent_state = graph.propagator.create_initial_state(
            request.ticker, request.analysis_date, report_length=request.report_length
        )
        args = graph.propagator.get_graph_args()

        # Initialize agent statuses
        agent_status = {
            "Market Analyst": "pending",
            "Social Analyst": "pending",
            "News Analyst": "pending",
            "Fundamentals Analyst": "pending",
            "Bull Researcher": "pending",
            "Bear Researcher": "pending",
            "Research Manager": "pending",
            "Trader": "pending",
            "Risky Analyst": "pending",
            "Neutral Analyst": "pending",
            "Safe Analyst": "pending",
            "Portfolio Manager": "pending",
        }

        # Send initial status
        await send_update(websocket, "status", {
            "message": f"Starting analysis for {request.ticker} on {request.analysis_date}",
            "agents": agent_status
        })

        # Track report sections
        report_sections = {
            "market_report": None,
            "sentiment_report": None,
            "news_report": None,
            "fundamentals_report": None,
            "investment_plan": None,
            "trader_investment_plan": None,
            "final_trade_decision": None,
        }

        # Stream the analysis with rate limiting
        trace = []
        last_request_time = 0
        # Hardcoded to use DeepSeek rate limiting (2 seconds interval)
        min_request_interval = config.get("rate_limit_interval", 2.0)  # DeepSeek has better rate limits
        
        # Add initial delay before starting stream to avoid immediate quota hits
        # This gives time for any previous requests to clear and prevents rapid-fire initialization
        await asyncio.sleep(1.0)  # Brief delay before first API call
        
        # Stream with enhanced rate limiting
        for chunk in graph.graph.stream(init_agent_state, **args):
            # Rate limiting: Add delay between chunks to avoid ResourceExhausted errors
            # This ensures we never exceed the rate limits
            current_time = time.time()
            time_since_last = current_time - last_request_time
            if time_since_last < min_request_interval:
                sleep_time = min_request_interval - time_since_last
                # Use asyncio.sleep for non-blocking delay
                await asyncio.sleep(sleep_time)
            last_request_time = time.time()
            if len(chunk.get("messages", [])) > 0:
                # Get the last message from the chunk
                last_message = chunk["messages"][-1]

                # Extract message content
                if hasattr(last_message, "content"):
                    content = extract_content_string(last_message.content)
                    msg_type = "Reasoning"
                else:
                    content = str(last_message)
                    msg_type = "System"

                # Send message update
                await send_update(websocket, "message", {
                    "type": msg_type,
                    "content": content
                })

                # Handle tool calls
                if hasattr(last_message, "tool_calls"):
                    for tool_call in last_message.tool_calls:
                        if isinstance(tool_call, dict):
                            tool_name = tool_call.get("name", "unknown")
                            tool_args = tool_call.get("args", {})
                        else:
                            tool_name = tool_call.name
                            tool_args = tool_call.args

                        await send_update(websocket, "tool_call", {
                            "name": tool_name,
                            "args": tool_args
                        })

                # Update agent statuses and reports based on chunk content
                # Analyst Team Reports
                if "market_report" in chunk and chunk["market_report"]:
                    report_sections["market_report"] = chunk["market_report"]
                    agent_status["Market Analyst"] = "completed"
                    # Save report
                    with open(report_dir / "market_report.md", "w", encoding="utf-8") as f:
                        f.write(chunk["market_report"])
                    
                    await send_update(websocket, "report", {
                        "section": "market_report",
                        "label": "Market Analysis",
                        "content": chunk["market_report"]
                    })
                    
                    if request.analysts and "social" in request.analysts:
                        agent_status["Social Analyst"] = "in_progress"
                    await send_update(websocket, "status", {"agents": agent_status})

                if "sentiment_report" in chunk and chunk["sentiment_report"]:
                    report_sections["sentiment_report"] = chunk["sentiment_report"]
                    agent_status["Social Analyst"] = "completed"
                    # Save report
                    with open(report_dir / "sentiment_report.md", "w", encoding="utf-8") as f:
                        f.write(chunk["sentiment_report"])
                    
                    await send_update(websocket, "report", {
                        "section": "sentiment_report",
                        "label": "Social Sentiment",
                        "content": chunk["sentiment_report"]
                    })
                    
                    if request.analysts and "news" in request.analysts:
                        agent_status["News Analyst"] = "in_progress"
                    await send_update(websocket, "status", {"agents": agent_status})

                if "news_report" in chunk and chunk["news_report"]:
                    report_sections["news_report"] = chunk["news_report"]
                    agent_status["News Analyst"] = "completed"
                    # Save report
                    with open(report_dir / "news_report.md", "w", encoding="utf-8") as f:
                        f.write(chunk["news_report"])
                    
                    await send_update(websocket, "report", {
                        "section": "news_report",
                        "label": "News Analysis",
                        "content": chunk["news_report"]
                    })
                    
                    if request.analysts and "fundamentals" in request.analysts:
                        agent_status["Fundamentals Analyst"] = "in_progress"
                    await send_update(websocket, "status", {"agents": agent_status})

                if "fundamentals_report" in chunk and chunk["fundamentals_report"]:
                    report_sections["fundamentals_report"] = chunk["fundamentals_report"]
                    agent_status["Fundamentals Analyst"] = "completed"
                    # Save report
                    with open(report_dir / "fundamentals_report.md", "w", encoding="utf-8") as f:
                        f.write(chunk["fundamentals_report"])
                    
                    await send_update(websocket, "report", {
                        "section": "fundamentals_report",
                        "label": "Fundamentals Review",
                        "content": chunk["fundamentals_report"]
                    })
                    
                    # Start research team
                    agent_status["Bull Researcher"] = "in_progress"
                    agent_status["Bear Researcher"] = "in_progress"
                    agent_status["Research Manager"] = "in_progress"
                    await send_update(websocket, "status", {"agents": agent_status})

                # Research Team - Handle Investment Debate State
                if "investment_debate_state" in chunk and chunk["investment_debate_state"] is not None:
                    debate_state = chunk["investment_debate_state"]
                    
                    # Safety check: ensure debate_state is a dict
                    if not isinstance(debate_state, dict):
                        debate_state = {}

                    # Update Bull Researcher status and report
                    if debate_state and "bull_history" in debate_state and debate_state.get("bull_history"):
                        agent_status["Bull Researcher"] = "in_progress"
                        agent_status["Bear Researcher"] = "in_progress"
                        agent_status["Research Manager"] = "in_progress"
                        await send_update(websocket, "status", {"agents": agent_status})
                        
                        # Extract latest bull response
                        bull_responses = debate_state["bull_history"].split("\n")
                        latest_bull = bull_responses[-1] if bull_responses else ""
                        if latest_bull:
                            await send_update(websocket, "message", {
                                "type": "Reasoning",
                                "content": latest_bull
                            })
                            
                            # Update research report with bull's latest analysis
                            current_plan = report_sections.get("investment_plan") or ""
                            if "Bull Researcher Analysis" not in current_plan:
                                report_sections["investment_plan"] = f"### Bull Researcher Analysis\n{latest_bull}"
                            else:
                                # Update existing bull section
                                parts = current_plan.split("### Bear Researcher Analysis")
                                report_sections["investment_plan"] = f"{parts[0].split('### Bull Researcher Analysis')[0]}### Bull Researcher Analysis\n{latest_bull}" + (f"\n\n### Bear Researcher Analysis{parts[1]}" if len(parts) > 1 else "")
                            
                            await send_update(websocket, "report", {
                                "section": "investment_plan",
                                "label": "Research Team Decision",
                                "content": report_sections["investment_plan"]
                            })

                    # Update Bear Researcher status and report
                    if debate_state and "bear_history" in debate_state and debate_state.get("bear_history"):
                        agent_status["Bull Researcher"] = "in_progress"
                        agent_status["Bear Researcher"] = "in_progress"
                        agent_status["Research Manager"] = "in_progress"
                        await send_update(websocket, "status", {"agents": agent_status})
                        
                        # Extract latest bear response
                        bear_responses = debate_state["bear_history"].split("\n")
                        latest_bear = bear_responses[-1] if bear_responses else ""
                        if latest_bear:
                            await send_update(websocket, "message", {
                                "type": "Reasoning",
                                "content": latest_bear
                            })
                            
                            # Update research report with bear's latest analysis
                            current_plan = report_sections.get("investment_plan") or ""
                            if "Bear Researcher Analysis" not in current_plan:
                                report_sections["investment_plan"] = f"{current_plan}\n\n### Bear Researcher Analysis\n{latest_bear}"
                            else:
                                # Update existing bear section
                                parts = current_plan.split("### Bear Researcher Analysis")
                                report_sections["investment_plan"] = parts[0] + f"\n\n### Bear Researcher Analysis\n{latest_bear}"
                            
                            await send_update(websocket, "report", {
                                "section": "investment_plan",
                                "label": "Research Team Decision",
                                "content": report_sections["investment_plan"]
                            })

                    # Update Research Manager status and final decision
                    if debate_state and "judge_decision" in debate_state and debate_state.get("judge_decision"):
                        agent_status["Bull Researcher"] = "completed"
                        agent_status["Bear Researcher"] = "completed"
                        agent_status["Research Manager"] = "completed"
                        
                        # Append judge decision to investment plan
                        current_plan = report_sections.get("investment_plan") or ""
                        report_sections["investment_plan"] = f"{current_plan}\n\n### Research Manager Decision\n{debate_state['judge_decision']}"
                        
                        # Save report
                        with open(report_dir / "investment_plan.md", "w", encoding="utf-8") as f:
                            f.write(report_sections["investment_plan"])
                        
                        await send_update(websocket, "report", {
                            "section": "investment_plan",
                            "label": "Research Team Decision",
                            "content": report_sections["investment_plan"]
                        })
                        
                        await send_update(websocket, "message", {
                            "type": "Reasoning",
                            "content": f"Research Manager: {debate_state['judge_decision']}"
                        })
                        
                        agent_status["Trader"] = "in_progress"
                        await send_update(websocket, "status", {"agents": agent_status})

                # Trading Team
                if "trader_investment_plan" in chunk and chunk["trader_investment_plan"]:
                    report_sections["trader_investment_plan"] = chunk["trader_investment_plan"]
                    agent_status["Trader"] = "completed"
                    # Save report
                    with open(report_dir / "trader_investment_plan.md", "w", encoding="utf-8") as f:
                        f.write(chunk["trader_investment_plan"])
                    
                    await send_update(websocket, "report", {
                        "section": "trader_investment_plan",
                        "label": "Trader Investment Plan",
                        "content": chunk["trader_investment_plan"]
                    })
                    
                    agent_status["Risky Analyst"] = "in_progress"
                    await send_update(websocket, "status", {"agents": agent_status})

                # Risk Management Team
                if "risk_debate_state" in chunk and chunk["risk_debate_state"] is not None:
                    risk_state = chunk["risk_debate_state"]
                    
                    # Safety check: ensure risk_state is a dict
                    if not isinstance(risk_state, dict):
                        risk_state = {}

                    if risk_state and "current_risky_response" in risk_state and risk_state.get("current_risky_response"):
                        agent_status["Risky Analyst"] = "in_progress"
                        await send_update(websocket, "status", {"agents": agent_status})
                        await send_update(websocket, "message", {
                            "type": "Reasoning",
                            "content": f"Risky Analyst: {risk_state['current_risky_response']}"
                        })

                    if risk_state and "current_safe_response" in risk_state and risk_state.get("current_safe_response"):
                        agent_status["Safe Analyst"] = "in_progress"
                        await send_update(websocket, "status", {"agents": agent_status})
                        await send_update(websocket, "message", {
                            "type": "Reasoning",
                            "content": f"Safe Analyst: {risk_state['current_safe_response']}"
                        })

                    if risk_state and "current_neutral_response" in risk_state and risk_state.get("current_neutral_response"):
                        agent_status["Neutral Analyst"] = "in_progress"
                        await send_update(websocket, "status", {"agents": agent_status})
                        await send_update(websocket, "message", {
                            "type": "Reasoning",
                            "content": f"Neutral Analyst: {risk_state['current_neutral_response']}"
                        })

                    if risk_state and "judge_decision" in risk_state and risk_state.get("judge_decision"):
                        agent_status["Risky Analyst"] = "completed"
                        agent_status["Safe Analyst"] = "completed"
                        agent_status["Neutral Analyst"] = "completed"
                        agent_status["Portfolio Manager"] = "completed"
                        
                        # Build final decision report with all risk analysis
                        current_decision = report_sections.get("final_trade_decision") or ""
                        if "Portfolio Manager Decision" not in current_decision:
                            report_sections["final_trade_decision"] = f"{current_decision}\n\n### Portfolio Manager Decision\n{risk_state['judge_decision']}"
                        else:
                            # Update existing decision
                            parts = current_decision.split("### Portfolio Manager Decision")
                            report_sections["final_trade_decision"] = parts[0] + f"\n\n### Portfolio Manager Decision\n{risk_state['judge_decision']}"
                        
                        # Save report
                        with open(report_dir / "final_trade_decision.md", "w", encoding="utf-8") as f:
                            f.write(report_sections["final_trade_decision"])
                        
                        await send_update(websocket, "report", {
                            "section": "final_trade_decision",
                            "label": "Portfolio Management Decision",
                            "content": report_sections["final_trade_decision"]
                        })
                        
                        await send_update(websocket, "message", {
                            "type": "Reasoning",
                            "content": f"Portfolio Manager: {risk_state['judge_decision']}"
                        })
                        
                        await send_update(websocket, "status", {"agents": agent_status})

            trace.append(chunk)

        # Get final state and decision
        final_state = trace[-1]
        decision = graph.process_signal(final_state.get("final_trade_decision", ""))

        # Send completion
        await send_update(websocket, "complete", {
            "decision": decision,
            "final_state": {
                "market_report": report_sections.get("market_report"),
                "sentiment_report": report_sections.get("sentiment_report"),
                "news_report": report_sections.get("news_report"),
                "fundamentals_report": report_sections.get("fundamentals_report"),
                "investment_plan": report_sections.get("investment_plan"),
                "trader_investment_plan": report_sections.get("trader_investment_plan"),
                "final_trade_decision": report_sections.get("final_trade_decision"),
            }
        })

        # Store current state for reflection
        curr_state = final_state

        print("📝 Summarizing Reports with Typhoon...")
        try:
            summarizer_func = create_summarizer_fundamental()
            sum_market = create_summarizer_market()
            sum_social = create_summarizer_social()
            sum_news = create_summarizer_news()
            sum_cons = create_summarizer_conservative()
            sum_aggr = create_summarizer_aggressive()
            sum_neut = create_summarizer_neutral()
            sum_investment_plan = create_summarizer_research_manager()
            sum_risk_plan = create_summarizer_risk_manager()
            sum_bull = create_summarizer_bull_researcher()
            sum_bear = create_summarizer_bear_researcher()
            sum_trader = create_summarizer_trader()
            
            update_dict_fund = summarizer_func(final_state)
            update_dict_market = sum_market(final_state)
            update_dict_social = sum_social(final_state)
            update_dict_news = sum_news(final_state)
            update_dict_cons = sum_cons(final_state)
            update_dict_aggr = sum_aggr(final_state)
            update_dict_neut = sum_neut(final_state)
            update_dict_investment_plan = sum_investment_plan(final_state)
            update_dict_risk_plan = sum_risk_plan(final_state)
            update_dict_bull = sum_bull(final_state)
            update_dict_bear = sum_bear(final_state)
            update_dict_trader = sum_trader(final_state)
            
            
            # --- อัปเดต Fundamental ---
            if update_dict_fund:
                final_state.update(update_dict_fund)
                curr_state.update(update_dict_fund)
                print("✅ Fundamental Summary Updated!")
            else:
                print("⚠️ Fundamental Summary returned empty.")

            # --- อัปเดต Market ---
            if update_dict_market:
                final_state.update(update_dict_market)
                curr_state.update(update_dict_market)
                print("✅ Market Summary Updated!")
            else:
                print("⚠️ Market Summary returned empty.")

            # --- อัปเดต Social ---
            if update_dict_social:
                final_state.update(update_dict_social)
                curr_state.update(update_dict_social)
                print("✅ Social Summary Updated!")
            else:
                print("⚠️ Social Summary returned empty.")

            # --- อัปเดต News ---
            if update_dict_news:
                final_state.update(update_dict_news)
                curr_state.update(update_dict_news)
                print("✅ News Summary Updated!")
            else:
                print("⚠️ News Summary returned empty.")

            # --- อัปเดต Conservative ---
            if update_dict_cons:
                final_state.update(update_dict_cons)
                curr_state.update(update_dict_cons)
                print("✅ Conservative Summary Updated!")
            else:
                print("⚠️ Conservative Summary returned empty.")
            
            # --- อัปเดต Aggressive ---
            if update_dict_aggr:
                final_state.update(update_dict_aggr)
                curr_state.update(update_dict_aggr)
                print("✅ Aggressive Summary Updated!")
            else:
                print("⚠️ Aggressive Summary returned empty.")

            # --- อัปเดต Neutral ---
            if update_dict_neut:
                final_state.update(update_dict_neut)
                curr_state.update(update_dict_neut)
                print("✅ Neutral Summary Updated!")
            else:
                print("⚠️ Neutral Summary returned empty.")

            # --- อัปเดต Investment Plan ---
            if update_dict_investment_plan:
                final_state.update(update_dict_investment_plan)
                curr_state.update(update_dict_investment_plan)
                print("✅ Investment Plan Summary Updated!")
            else:
                print("⚠️ Investment Plan Summary returned empty.")
            
            # --- อัปเดต Risk Plan ---
            if update_dict_risk_plan:
                final_state.update(update_dict_risk_plan)
                curr_state.update(update_dict_risk_plan)
                print("✅ Risk Plan Summary Updated!")
            else:
                print("⚠️ Risk Plan Summary returned empty.")
                
            # --- อัปเดต bull ---
            if update_dict_bull:
                final_state.update(update_dict_bull)
                curr_state.update(update_dict_bull)
                print("✅ bull Summary Updated!")
            else:
                print("⚠️ bull Summary returned empty.")
                
            # --- อัปเดต bear ---
            if update_dict_bear:
                final_state.update(update_dict_bear)
                curr_state.update(update_dict_bear)
                print("✅ bear Summary Updated!")
            else:
                print("⚠️ bear Summary returned empty.")
                
            # --- อัปเดต trader ---
            if update_dict_trader:
                final_state.update(update_dict_trader)
                curr_state.update(update_dict_trader)
                print("✅ trader Summary Updated!")
            else:
                print("⚠️ trader Summary returned empty.")
                
            print("📝 Sent telegram...")    
            # read text and send to telegram
            with open("all_report_message.txt", "r", encoding="utf-8") as f:
                report_messages = f.read()
                sent_to_telegram(report_messages)
                
        except Exception as e:
            print(f"❌ Failed to summarize: {e}")


        sum_finda = final_state.get("Summarize_fundamentals_report")
        funda = final_state.get("fundamentals_report")
        
        sum_market = final_state.get("Summarize_market_report")
        market = final_state.get("market_report")

        sum_cial = final_state.get("Summarize_social_report")
        social = final_state.get("sentiment_report")

        sum_news = final_state.get("Summarize_news_report")
        news = final_state.get("news_report")
        
        with open("./sum_funda.txt", 'w', encoding='utf-8') as f:
            f.write(str(sum_finda))
            
        funda = json.loads(funda)
        with open("./full_funda.json", 'w', encoding='utf-8') as f:
            json.dump(funda, f, ensure_ascii=False, indent=4)
            
        with open("./sum_market.txt", 'w', encoding='utf-8') as f:
            f.write(str(sum_market))
            
        market = json.loads(market)
        with open("./full_market.json", 'w', encoding='utf-8') as f:
            json.dump(market, f, ensure_ascii=False, indent=4)

        with open("./sum_social.txt", 'w', encoding='utf-8') as f:
            f.write(str(sum_cial))

        social = json.loads(social)
        with open("./full_social.json", 'w', encoding='utf-8') as f:
            json.dump(social, f, ensure_ascii=False, indent=4)

        with open("./sum_news.txt", 'w', encoding='utf-8') as f:
            f.write(str(sum_news))
        
        news = json.loads(news)
        with open("./full_news.json", 'w', encoding='utf-8') as f:
            json.dump(news, f, ensure_ascii=False, indent=4)

        investment = final_state.get("investment_debate_state")
        risk = final_state.get("risk_debate_state")
        trader = final_state.get("trader_investment_decision")
    
        
        # เขียนให้เป็น JSON สวยๆ (pretty)
        with open("./investment.json", "w", encoding="utf-8") as f:
            json.dump(investment, f, ensure_ascii=False, indent=4)

        with open("./risk.json", "w", encoding="utf-8") as f:
            json.dump(risk, f, ensure_ascii=False, indent=4)
            
        with open("./trader.json", "w", encoding="utf-8") as f:
            json.dump(trader, f, ensure_ascii=False, indent=4)

    except Exception as e:
        await send_update(websocket, "error", {
            "message": str(e)
        })
        raise


# Create FastAPI app
app = FastAPI(
    title="TradingAgents API",
    version="1.0.0",
    description="""
    TradingAgents API provides real-time trading analysis through WebSocket connections.
    
    ## Frontend Applications
    
    * **React Frontend**: `/web/` - Modern React + Vite application
    * **Legacy Frontend**: `/legacy` - Vanilla JavaScript version
    
    ## Quick Links
    
    * [React Frontend](/web/) - Main web interface
    * [Legacy Frontend](/legacy) - Legacy vanilla JS version
    * [API Documentation](/docs) - Interactive API documentation
    * [Alternative Docs](/redoc) - Alternative API documentation
    
    ## WebSocket
    
    Connect to `/ws` for real-time analysis updates. Send analysis requests and receive:
    - Agent status updates
    - Report sections as they're generated
    - Final analysis results
    """,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for web interface
# Check for production build (dist folder) first, then fall back to web directory
if WEB_DIST_DIR.exists():
    # Production build - serve from dist folder
    app.mount("/web", StaticFiles(directory=str(WEB_DIST_DIR), html=True), name="web")
elif WEB_DIR.exists():
    # Development - serve from web directory
    app.mount("/web", StaticFiles(directory=str(WEB_DIR), html=True), name="web")


@app.get("/", tags=["Frontend"], summary="Web Interface", description="Main web interface - React application")
async def root():
    """Serve the web interface at root."""
    # Check for production build first (React app)
    if WEB_DIST_DIR.exists():
        index_path = WEB_DIST_DIR / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
    elif WEB_DIR.exists():
        index_path = WEB_DIR / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
    return RedirectResponse(url="/web/")


@app.get("/legacy", tags=["Frontend"], summary="Legacy Web Interface", description="Legacy vanilla JavaScript version of the web interface")
async def serve_legacy():
    """Serve the legacy vanilla JS version."""
    if WEB_DIR.exists():
        legacy_path = WEB_DIR / "legacy.html"
        if legacy_path.exists():
            return FileResponse(str(legacy_path))
    raise HTTPException(status_code=404, detail="Legacy HTML file not found")


@app.get("/api/frontend", tags=["Frontend"], summary="Redirect to React Frontend", description="Redirects to the React web application at /web/")
async def redirect_to_frontend():
    """Redirect to the React frontend."""
    return RedirectResponse(url="/web/", status_code=302)


@app.get("/api/legacy-frontend", tags=["Frontend"], summary="Redirect to Legacy Frontend", description="Redirects to the legacy vanilla JavaScript web application at /legacy")
async def redirect_to_legacy():
    """Redirect to the legacy frontend."""
    return RedirectResponse(url="/legacy", status_code=302)


@app.get("/styles.css")
async def serve_styles():
    """Serve CSS file at root level."""
    # Check dist first (React build), then web directory
    if WEB_DIST_DIR.exists():
        css_path = WEB_DIST_DIR / "styles.css"
        if css_path.exists():
            return FileResponse(str(css_path), media_type="text/css")
    if WEB_DIR.exists():
        css_path = WEB_DIR / "src" / "styles.css"
        if css_path.exists():
            return FileResponse(str(css_path), media_type="text/css")
        # Fallback to root styles.css for legacy
        css_path = WEB_DIR / "styles.css"
        if css_path.exists():
            return FileResponse(str(css_path), media_type="text/css")
    raise HTTPException(status_code=404, detail="CSS file not found")


@app.get("/script.js")
async def serve_script():
    """Serve JavaScript file at root level."""
    if WEB_DIR.exists():
        js_path = WEB_DIR / "script.js"
        if js_path.exists():
            return FileResponse(str(js_path), media_type="application/javascript")
    raise HTTPException(status_code=404, detail="JavaScript file not found")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time analysis updates.
    
    Connect to receive live status updates, reports, and analysis results.
    Send analysis requests in JSON format with action: "start_analysis".
    """
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Wait for analysis request
            data = await websocket.receive_json()
            
            if data.get("action") == "start_analysis":
                request_data = data.get("request")
                if not request_data:
                    await send_update(websocket, "error", {"message": "Missing request data"})
                    continue
                
                # Create request model
                try:
                    request = AnalysisRequest(**request_data)
                except Exception as e:
                    await send_update(websocket, "error", {"message": f"Invalid request: {str(e)}"})
                    continue
                
                # Run analysis in background
                await run_analysis_stream(websocket, request)
                
            elif data.get("action") == "ping":
                await send_update(websocket, "pong", {})
                
    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)


@app.get("/.well-known/appspecific/com.chrome.devtools.json")
async def chrome_devtools_config():
    """Handle Chrome DevTools configuration request."""
    # Return empty JSON to satisfy Chrome DevTools
    return {}


@app.get("/api/health", tags=["System"], summary="Health Check", description="Check API health status and active connections")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "connections": len(active_connections),
        "project_root": str(PROJECT_ROOT),
        "web_dir_exists": WEB_DIR.exists(),
        "web_dist_exists": WEB_DIST_DIR.exists() if WEB_DIST_DIR else False,
        "frontend_urls": {
            "react": "/web/",
            "legacy": "/legacy"
        }
    }


@app.get("/api/test", tags=["System"], summary="Test Endpoint", description="Test endpoint to verify API and imports are working correctly")
async def test_endpoint():
    """Test endpoint to verify API is working."""
    try:
        # Test imports
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        from tradingagents.default_config import DEFAULT_CONFIG
        
        return {
            "status": "ok",
            "message": "API is working correctly",
            "tradingagents_imported": True,
            "config_loaded": True
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

