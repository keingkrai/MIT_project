# TradingAgents/graph/trading_graph.py

import os
from pathlib import Path
import json
from datetime import date
from typing import Dict, Any, Tuple, List, Optional

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

from langgraph.prebuilt import ToolNode

from tradingagents.agents import *
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.agents.utils.memory import FinancialSituationMemory
from tradingagents.agents.utils.agent_states import (
    AgentState,
    InvestDebateState,
    RiskDebateState,
)
from tradingagents.dataflows.config import set_config

# Import the new abstract tool methods from agent_utils
from tradingagents.agents.utils.agent_utils import (
    get_stock_data,
    get_indicators,
    get_fundamentals,
    get_balance_sheet,
    get_cashflow,
    get_income_statement,
    get_news,
    get_insider_sentiment,
    get_insider_transactions,
    get_global_news,
    get_social
)

from .conditional_logic import ConditionalLogic
from .setup import GraphSetup
from .propagation import Propagator
from .reflection import Reflector
from .signal_processing import SignalProcessor


class TradingAgentsGraph:
    """Main class that orchestrates the trading agents framework."""

    def __init__(
        self,
        selected_analysts=["market", "social", "news", "fundamentals"],
        debug=False,
        config: Dict[str, Any] = None,
    ):
        """Initialize the trading agents graph and components.

        Args:
            selected_analysts: List of analyst types to include
            debug: Whether to run in debug mode
            config: Configuration dictionary. If None, uses default config
        """
        self.debug = debug
        self.config = config or DEFAULT_CONFIG

        # Update the interface's config
        set_config(self.config)

        # Create necessary directories
        os.makedirs(
            os.path.join(self.config["project_dir"], "dataflows/data_cache"),
            exist_ok=True,
        )

        # Initialize LLMs
        if self.config["llm_provider"].lower() == "openai" or self.config["llm_provider"] == "ollama" or self.config["llm_provider"] == "openrouter":
            self.deep_thinking_llm = ChatOpenAI(model=self.config["deep_think_llm"], base_url=self.config["backend_url"])
            self.quick_thinking_llm = ChatOpenAI(model=self.config["quick_think_llm"], base_url=self.config["backend_url"])
        elif self.config["llm_provider"].lower() == "anthropic":
            self.deep_thinking_llm = ChatAnthropic(model=self.config["deep_think_llm"], base_url=self.config["backend_url"])
            self.quick_thinking_llm = ChatAnthropic(model=self.config["quick_think_llm"], base_url=self.config["backend_url"])
        elif self.config["llm_provider"].lower() == "google":
            self.deep_thinking_llm = ChatGoogleGenerativeAI(model=self.config["deep_think_llm"])
            self.quick_thinking_llm = ChatGoogleGenerativeAI(model=self.config["quick_think_llm"])
        elif self.config["llm_provider"].lower() == "typhoon":
            self.deep_thinking_llm = ChatOpenAI(model=self.config["deep_think_llm"], base_url=self.config["backend_url"])
            self.quick_thinking_llm = ChatOpenAI(model=self.config["quick_think_llm"], base_url=self.config["backend_url"])
        else:
            raise ValueError(f"Unsupported LLM provider: {self.config['llm_provider']}")
        
        # Initialize memories
        self.bull_memory = FinancialSituationMemory("bull_memory", self.config)
        self.bear_memory = FinancialSituationMemory("bear_memory", self.config)
        self.trader_memory = FinancialSituationMemory("trader_memory", self.config)
        self.invest_judge_memory = FinancialSituationMemory("invest_judge_memory", self.config)
        self.risk_manager_memory = FinancialSituationMemory("risk_manager_memory", self.config)

        # Create tool nodes
        self.tool_nodes = self._create_tool_nodes()

        # Initialize components
        self.conditional_logic = ConditionalLogic()
        self.graph_setup = GraphSetup(
            self.quick_thinking_llm,
            self.deep_thinking_llm,
            self.tool_nodes,
            self.bull_memory,
            self.bear_memory,
            self.trader_memory,
            self.invest_judge_memory,
            self.risk_manager_memory,
            self.conditional_logic,
        )

        self.propagator = Propagator()
        self.reflector = Reflector(self.quick_thinking_llm)
        self.signal_processor = SignalProcessor(self.quick_thinking_llm)

        # State tracking
        self.curr_state = None
        self.ticker = None
        self.log_states_dict = {}  # date to full state dict

        # Set up the graph
        self.graph = self.graph_setup.setup_graph(selected_analysts)

    def _create_tool_nodes(self) -> Dict[str, ToolNode]:
        """Create tool nodes for different data sources using abstract methods."""
        return {
            "market": ToolNode(
                [
                    # Core stock data tools
                    get_stock_data,
                    # Technical indicators
                    get_indicators,
                ]
            ),
            "social": ToolNode(
                [
                    # News tools for social media analysis
                    get_news,
                    get_social
                ]
            ),
            "news": ToolNode(
                [
                    # News and insider information
                    get_news,
                    get_global_news,
                    get_insider_sentiment,
                    get_insider_transactions,
                ]
            ),
            "fundamentals": ToolNode(
                [
                    # Fundamental analysis tools
                    get_fundamentals,
                    get_balance_sheet,
                    get_cashflow,
                    get_income_statement,
                ]
            ),
        }

    def propagate(self, company_name, trade_date):
        """Run the trading agents graph for a company on a specific date."""

        self.ticker = company_name

        # Initialize state
        init_agent_state = self.propagator.create_initial_state(
            company_name, trade_date
        )
        args = self.propagator.get_graph_args()

        if self.debug:
            # Debug mode with tracing
            trace = []
            for chunk in self.graph.stream(init_agent_state, **args):
                if len(chunk["messages"]) == 0:
                    pass
                else:
                    chunk["messages"][-1].pretty_print()
                    trace.append(chunk)

            final_state = trace[-1]
        else:
            # Standard mode without tracing
            final_state = self.graph.invoke(init_agent_state, **args)

        # Store current state for reflection
        self.curr_state = final_state
        
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
                self.curr_state.update(update_dict_fund)
                print("✅ Fundamental Summary Updated!")
            else:
                print("⚠️ Fundamental Summary returned empty.")

            # --- อัปเดต Market ---
            if update_dict_market:
                final_state.update(update_dict_market)
                self.curr_state.update(update_dict_market)
                print("✅ Market Summary Updated!")
            else:
                print("⚠️ Market Summary returned empty.")

            # --- อัปเดต Social ---
            if update_dict_social:
                final_state.update(update_dict_social)
                self.curr_state.update(update_dict_social)
                print("✅ Social Summary Updated!")
            else:
                print("⚠️ Social Summary returned empty.")

            # --- อัปเดต News ---
            if update_dict_news:
                final_state.update(update_dict_news)
                self.curr_state.update(update_dict_news)
                print("✅ News Summary Updated!")
            else:
                print("⚠️ News Summary returned empty.")

            # --- อัปเดต Conservative ---
            if update_dict_cons:
                final_state.update(update_dict_cons)
                self.curr_state.update(update_dict_cons)
                print("✅ Conservative Summary Updated!")
            else:
                print("⚠️ Conservative Summary returned empty.")
            
            # --- อัปเดต Aggressive ---
            if update_dict_aggr:
                final_state.update(update_dict_aggr)
                self.curr_state.update(update_dict_aggr)
                print("✅ Aggressive Summary Updated!")
            else:
                print("⚠️ Aggressive Summary returned empty.")

            # --- อัปเดต Neutral ---
            if update_dict_neut:
                final_state.update(update_dict_neut)
                self.curr_state.update(update_dict_neut)
                print("✅ Neutral Summary Updated!")
            else:
                print("⚠️ Neutral Summary returned empty.")

            # --- อัปเดต Investment Plan ---
            if update_dict_investment_plan:
                final_state.update(update_dict_investment_plan)
                self.curr_state.update(update_dict_investment_plan)
                print("✅ Investment Plan Summary Updated!")
            else:
                print("⚠️ Investment Plan Summary returned empty.")
            
            # --- อัปเดต Risk Plan ---
            if update_dict_risk_plan:
                final_state.update(update_dict_risk_plan)
                self.curr_state.update(update_dict_risk_plan)
                print("✅ Risk Plan Summary Updated!")
            else:
                print("⚠️ Risk Plan Summary returned empty.")
                
            # --- อัปเดต bull ---
            if update_dict_bull:
                final_state.update(update_dict_bull)
                self.curr_state.update(update_dict_bull)
                print("✅ bull Summary Updated!")
            else:
                print("⚠️ bull Summary returned empty.")
                
            # --- อัปเดต bear ---
            if update_dict_bear:
                final_state.update(update_dict_bear)
                self.curr_state.update(update_dict_bear)
                print("✅ bear Summary Updated!")
            else:
                print("⚠️ bear Summary returned empty.")
                
            # --- อัปเดต trader ---
            if update_dict_trader:
                final_state.update(update_dict_trader)
                self.curr_state.update(update_dict_trader)
                print("✅ trader Summary Updated!")
            else:
                print("⚠️ trader Summary returned empty.")
                
        except Exception as e:
            print(f"❌ Failed to summarize: {e}")
        # Log state
        self._log_state(trade_date, final_state)

        # Return decision and processed signal
        return final_state, self.process_signal(final_state["final_trade_decision"])

    def _log_state(self, trade_date, final_state):
        """Log the final state to a JSON file."""
        self.log_states_dict[str(trade_date)] = {
            "company_of_interest": final_state["company_of_interest"],
            "trade_date": final_state["trade_date"],
            "market_report": final_state["market_report"],
            "sentiment_report": final_state["sentiment_report"],
            "news_report": final_state["news_report"],
            "fundamentals_report": final_state["fundamentals_report"],
            "investment_debate_state": {
                "bull_history": final_state["investment_debate_state"]["bull_history"],
                "bear_history": final_state["investment_debate_state"]["bear_history"],
                "history": final_state["investment_debate_state"]["history"],
                "current_response": final_state["investment_debate_state"][
                    "current_response"
                ],
                "judge_decision": final_state["investment_debate_state"][
                    "judge_decision"
                ],
            },
            "trader_investment_decision": final_state["trader_investment_plan"],
            "risk_debate_state": {
                "risky_history": final_state["risk_debate_state"]["risky_history"],
                "safe_history": final_state["risk_debate_state"]["safe_history"],
                "neutral_history": final_state["risk_debate_state"]["neutral_history"],
                "history": final_state["risk_debate_state"]["history"],
                "judge_decision": final_state["risk_debate_state"]["judge_decision"],
            },
            "investment_plan": final_state["investment_plan"],
            "final_trade_decision": final_state["final_trade_decision"],
        }
        
        # Save to file
        directory = Path(f"eval_results/{self.ticker}/TradingAgentsStrategy_logs/")
        directory.mkdir(parents=True, exist_ok=True)

        with open(
            f"eval_results/{self.ticker}/TradingAgentsStrategy_logs/full_states_log_{trade_date}.json",
            "w",
        ) as f:
            json.dump(self.log_states_dict, f, indent=4)

    def reflect_and_remember(self, returns_losses):
        """Reflect on decisions and update memory based on returns."""
        self.reflector.reflect_bull_researcher(
            self.curr_state, returns_losses, self.bull_memory
        )
        self.reflector.reflect_bear_researcher(
            self.curr_state, returns_losses, self.bear_memory
        )
        self.reflector.reflect_trader(
            self.curr_state, returns_losses, self.trader_memory
        )
        self.reflector.reflect_invest_judge(
            self.curr_state, returns_losses, self.invest_judge_memory
        )
        self.reflector.reflect_risk_manager(
            self.curr_state, returns_losses, self.risk_manager_memory
        )

    def process_signal(self, full_signal):
        """Process a signal to extract the core decision."""
        return self.signal_processor.process_signal(full_signal)