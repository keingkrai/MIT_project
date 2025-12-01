# TradingAgents Project Structure Analysis

## 📁 Project Overview

**TradingAgents** is a Multi-Agents LLM Financial Trading Framework that uses specialized AI agents to analyze financial markets and make trading decisions.

## 🗂️ Directory Structure

### Root Level Files
- **`api_server.py`** - Flask REST API server for web frontend integration
- **`main.py`** - Example script showing how to use TradingAgents programmatically
- **`setup.py`** - Package installation configuration
- **`requirements.txt`** - Python dependencies (273 packages)
- **`README.md`** - Project documentation
- **`start_api_server.bat`** / **`start_api_server.sh`** - Server startup scripts

### 📂 Core Directories

#### 1. **`cli/`** - Command Line Interface
- **`main.py`** (1,110 lines) - Main CLI application with interactive prompts
- **`models.py`** - Data models (AnalystType enum)
- **`utils.py`** - Utility functions for user input (ticker, date, analyst selection)
- **`static/welcome.txt`** - ASCII art welcome message

**Purpose**: Provides an interactive terminal interface for running trading analysis.

#### 2. **`tradingagents/`** - Core Framework

##### **`agents/`** - AI Agent Implementations
- **`analysts/`**
  - `market_analyst.py` - Technical/market analysis
  - `social_media_analyst.py` - Social sentiment analysis
  - `news_analyst.py` - News and macro analysis
  - `fundamentals_analyst.py` - Financial fundamentals analysis

- **`researchers/`**
  - `bull_researcher.py` - Bullish perspective researcher
  - `bear_researcher.py` - Bearish perspective researcher

- **`managers/`**
  - `research_manager.py` - Coordinates research team
  - `risk_manager.py` - Risk assessment and management

- **`trader/`**
  - `trader.py` - Makes trading decisions based on analysis

- **`risk_mgmt/`**
  - `aggresive_debator.py` - Aggressive risk stance
  - `conservative_debator.py` - Conservative risk stance
  - `neutral_debator.py` - Neutral risk stance

- **`utils/`**
  - `agent_states.py` - State management for agents
  - `agent_utils.py` - Agent helper functions
  - `core_stock_tools.py` - Stock data tools
  - `fundamental_data_tools.py` - Fundamental analysis tools
  - `news_data_tools.py` - News data tools
  - `technical_indicators_tools.py` - Technical analysis tools
  - `memory.py` - Agent memory management

##### **`dataflows/`** - Data Source Integrations
- **Stock Data**: `y_finance.py`, `alpha_vantage_stock.py`, `core_stock_price.py`
- **News Data**: `alpha_vantage_news.py`, `googlenews_utils.py`, `reddit_utils.py`
- **Fundamentals**: `alpha_vantage_fundamentals.py`
- **Technical Indicators**: `alpha_vantage_indicator.py`, `stockstats_utils.py`
- **Trading View**: `trading_view.py`
- **LLM Interfaces**: `openai.py`, `local.py`, `local_call.py`
- **Config**: `config.py`, `interface.py`

##### **`graph/`** - LangGraph Workflow
- **`trading_graph.py`** - Main graph orchestration
- **`setup.py`** - Graph structure setup
- **`propagation.py`** - State propagation logic
- **`conditional_logic.py`** - Decision logic for graph edges
- **`reflection.py`** - Agent reflection capabilities
- **`signal_processing.py`** - Signal processing for decisions

##### **`default_config.py`** - Default configuration
- LLM provider settings (default: Typhoon)
- Data vendor configuration
- Debate rounds and limits

#### 3. **`data/`** - Sample Data
- **`fundamental/`** - Fundamental data for AAPL, NVDA, SPY
- **`stock/`** - Stock news data
- **`social/`** - Social media posts (Reddit, Mastodon, Bluesky)
- **`global_news/`** - World news data

#### 4. **`results/`** - Analysis Outputs
- Contains analysis results organized by ticker and date
- Each run creates:
  - `message_tool.log` - Execution log
  - `reports/` - Generated markdown reports:
    - `market_report.md`
    - `sentiment_report.md`
    - `news_report.md`
    - `fundamentals_report.md`
    - `investment_plan.md`
    - `trader_investment_plan.md`
    - `final_trade_decision.md`

#### 5. **`web/`** - Frontend Interface
- **`index.html`** - Main web interface (dark mode UI)
- **`script.js`** - Frontend JavaScript (connects to API server)
- **`styles.css`** - Styling for dark mode theme

#### 6. **`assets/`** - Images and Resources
- Project logos, diagrams, CLI screenshots

## 🔄 Workflow Architecture

### Agent Flow:
1. **Analyst Team** → Market, Social, News, Fundamentals analysis
2. **Research Team** → Bull/Bear debate → Research Manager decision
3. **Trader** → Creates investment plan
4. **Risk Management** → Risk assessment debate
5. **Portfolio Manager** → Final trade decision

### Data Flow:
- **Input**: Ticker symbol, analysis date
- **Processing**: Multi-agent analysis with LLM-powered agents
- **Output**: Comprehensive trading reports and final decision

## 🔧 Key Technologies

- **LangGraph** - Agent orchestration framework
- **LangChain** - LLM integration
- **Flask** - API server
- **Rich** - CLI UI library
- **Typer** - CLI framework
- **yfinance** / **Alpha Vantage** - Financial data sources

## 📊 Current Configuration

- **LLM Provider**: Typhoon (default)
- **Models**: `typhoon-v2.1-12b-instruct`
- **Data Sources**: Mix of local cached data and API sources
- **Debate Rounds**: 1 (configurable)

## 🚀 Usage Points

1. **CLI**: `python -m cli.main` - Interactive terminal interface
2. **API**: `python api_server.py` - REST API for web frontend
3. **Programmatic**: Import `TradingAgentsGraph` and use in Python code
4. **Web UI**: Open `web/index.html` in browser (requires API server)

## ⚠️ Important Notes

- Requires API keys (OpenAI, Alpha Vantage) in `.env` file
- Makes many LLM API calls (cost considerations)
- Designed for research purposes, not financial advice
- Results stored in `results/` directory




