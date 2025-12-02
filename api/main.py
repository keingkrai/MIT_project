"""
FastAPI backend for TradingAgents web interface.
Provides WebSocket support for real-time updates.
"""
import asyncio
import json
import datetime
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

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

# Active WebSocket connections
active_connections: List[WebSocket] = []


class AnalysisRequest(BaseModel):
    """Request model for starting an analysis."""
    ticker: str
    analysis_date: str
    analysts: List[str]  # List of analyst types: ["market", "social", "news", "fundamentals"]
    research_depth: int  # 1, 3, or 5
    llm_provider: str  # "openai", "anthropic", "google", etc.
    backend_url: str
    shallow_thinker: str
    deep_thinker: str


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
        config["quick_think_llm"] = request.shallow_thinker
        config["deep_think_llm"] = request.deep_thinker
        config["backend_url"] = request.backend_url
        config["llm_provider"] = request.llm_provider.lower()

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
            request.ticker, request.analysis_date
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

        # Stream the analysis
        trace = []
        for chunk in graph.graph.stream(init_agent_state, **args):
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

    except Exception as e:
        await send_update(websocket, "error", {
            "message": str(e)
        })
        raise


# Create FastAPI app
app = FastAPI(title="TradingAgents API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for web interface
if WEB_DIR.exists():
    app.mount("/web", StaticFiles(directory=str(WEB_DIR), html=True), name="web")


@app.get("/")
async def root():
    """Redirect to web interface."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/web/")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time analysis updates."""
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


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "connections": len(active_connections),
        "project_root": str(PROJECT_ROOT),
        "web_dir_exists": WEB_DIR.exists()
    }


@app.get("/api/test")
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

