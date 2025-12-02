# Frontend-Backend Connection Documentation

This document explains how the frontend (web interface) connects to the FastAPI backend in the MIT TradingAgents project.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Browser)                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  index.html + script.js + styles.css                 │  │
│  │  - User Interface                                    │  │
│  │  - WebSocket Client                                  │  │
│  │  - Real-time Updates Display                        │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────────┘
                        │ WebSocket (ws://localhost:8000/ws)
                        │ JSON Messages
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend (Python)                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  api/main.py                                         │  │
│  │  - WebSocket Server                                  │  │
│  │  - TradingAgentsGraph Integration                   │  │
│  │  - Real-time Status Updates                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                        │                                    │
│                        ▼                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  tradingagents/graph/trading_graph.py               │  │
│  │  - Agent Execution                                  │  │
│  │  - Report Generation                                │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Connection Flow

### 1. Server Startup

**File: `start_api.py`**
```python
uvicorn.run(
    "api.main:app",
    host="localhost",
    port=8000,
    reload=True
)
```

The FastAPI server starts on `http://localhost:8000`

### 2. Frontend WebSocket Connection

**File: `web/script.js` (lines 465-474)**

When the user clicks "Generate", the frontend establishes a WebSocket connection:

```javascript
// Determine WebSocket URL
let wsUrl;
if (window.location.protocol === "file:" || window.location.hostname === "") {
    // Running from file system, use localhost
    wsUrl = "ws://localhost:8000/ws";
} else {
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsHost = window.location.hostname;
    const wsPort = window.location.port || (window.location.protocol === "https:" ? "443" : "8000");
    wsUrl = `${wsProtocol}//${wsHost}:${wsPort}/ws`;
}

const ws = new WebSocket(wsUrl);
```

### 3. Backend WebSocket Endpoint

**File: `api/main.py` (lines 505-541)**

The backend accepts WebSocket connections at `/ws`:

```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("action") == "start_analysis":
                # Process analysis request
                request = AnalysisRequest(**data.get("request"))
                await run_analysis_stream(websocket, request)
```

## Message Protocol

### Frontend → Backend Messages

#### 1. Start Analysis Request

**Sent from:** `web/script.js` (lines 504-518)

```javascript
const request = {
    action: "start_analysis",
    request: {
        ticker: state.ticker,                    // e.g., "SPY"
        analysis_date: state.analysisDate,       // e.g., "2025-12-02"
        analysts: Array.from(state.analysts),    // ["market", "social", "news", "fundamentals"]
        research_depth: state.researchDepth,     // 1, 3, or 5
        llm_provider: state.llmProvider,        // "google"
        backend_url: state.backendUrl,          // Google Gemini API URL
        shallow_thinker: state.shallowModel,     // "gemini-2.0-flash-lite"
        deep_thinker: state.deepModel,          // "gemini-2.0-flash-lite"
    }
};
ws.send(JSON.stringify(request));
```

**Received by:** `api/main.py` (lines 516-530)

#### 2. Stop Analysis Request

**Sent from:** `web/script.js` (line 404)

```javascript
state.wsConnection.send(JSON.stringify({ action: "stop_analysis" }));
```

### Backend → Frontend Messages

All backend messages follow this structure:

```json
{
    "type": "<message_type>",
    "data": { ... },
    "timestamp": "2025-12-02T10:30:00.000000"
}
```

#### Message Types:

1. **`status`** - Agent status updates
   ```json
   {
       "type": "status",
       "data": {
           "message": "Starting analysis for SPY on 2025-12-02",
           "agents": {
               "Market Analyst": "pending",
               "Social Analyst": "in_progress",
               "News Analyst": "pending",
               ...
           }
       }
   }
   ```

2. **`message`** - General messages/reasoning
   ```json
   {
       "type": "message",
       "data": {
           "type": "Reasoning",
           "content": "Analyzing market trends..."
       }
   }
   ```

3. **`tool_call`** - Tool execution notifications
   ```json
   {
       "type": "tool_call",
       "data": {
           "name": "get_stock_data",
           "args": { "ticker": "SPY" }
       }
   }
   ```

4. **`report`** - Report section updates
   ```json
   {
       "type": "report",
       "data": {
           "section": "market_report",
           "label": "Market Analysis",
           "content": "# Market Analysis\n\n..."
       }
   }
   ```

5. **`complete`** - Analysis completion
   ```json
   {
       "type": "complete",
       "data": {
           "decision": "BUY",
           "final_state": {
               "market_report": "...",
               "sentiment_report": "...",
               ...
           }
       }
   }
   ```

6. **`error`** - Error notifications
   ```json
   {
       "type": "error",
       "data": {
           "message": "Error description"
       }
   }
   ```

7. **`pong`** - Keep-alive response
   ```json
   {
       "type": "pong",
       "data": {}
   }
   ```

## Frontend Message Handling

**File: `web/script.js` (lines 521-658)**

The frontend processes incoming messages in the `ws.onmessage` handler:

```javascript
ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    const { type, data } = message;
    
    switch (type) {
        case "status":
            // Update agent statuses in UI
            Object.entries(data.agents).forEach(([agentName, status]) => {
                updateAgentStatus(teamKey, frontendName, status);
            });
            break;
            
        case "report":
            // Add or update report section
            renderReportSections(reportSections);
            break;
            
        case "complete":
            // Analysis complete - update final state
            setRecommendation(data.decision);
            break;
            
        case "error":
            // Display error message
            elements.reportContent.innerHTML = `<p style="color: var(--danger)">Error: ${data.message}</p>`;
            break;
    }
};
```

## Agent Name Mapping

The backend uses different agent names than the frontend displays. Mapping is handled in `web/script.js` (lines 481-494):

```javascript
const agentToTeamMap = {
    "Market Analyst": ["analyst", "Market Analyst"],
    "Social Analyst": ["analyst", "Social Media Analyst"],
    "News Analyst": ["analyst", "News Analyst"],
    "Fundamentals Analyst": ["analyst", "Fundamentals Analyst"],
    "Bull Researcher": ["research", "Bull Research"],
    "Bear Researcher": ["research", "Bear Research"],
    "Research Manager": ["research", "Research Manager"],
    "Trader": ["trader", "Trader"],
    "Risky Analyst": ["risk", "Risk Analyst"],
    "Neutral Analyst": ["risk", "Neutral Analyst"],
    "Safe Analyst": ["risk", "Safe Analyst"],
    "Portfolio Manager": ["risk", "Portfolio Manager"],
};
```

## Analysis Execution Flow

1. **User clicks "Generate"** → Frontend connects to WebSocket
2. **Frontend sends `start_analysis`** → Backend receives request
3. **Backend initializes TradingAgentsGraph** → Creates agent graph
4. **Backend streams analysis** → Sends status/report updates
5. **Frontend updates UI** → Shows progress, reports, agent statuses
6. **Backend sends `complete`** → Analysis finished
7. **Frontend displays final decision** → Shows recommendation

## Key Files

### Frontend:
- `web/index.html` - HTML structure
- `web/script.js` - JavaScript logic and WebSocket client
- `web/styles.css` - Styling

### Backend:
- `start_api.py` - Server startup script
- `api/main.py` - FastAPI application and WebSocket handler
- `tradingagents/graph/trading_graph.py` - Core trading logic

## Testing the Connection

1. **Start the backend:**
   ```bash
   python start_api.py
   ```
   Server runs on `http://localhost:8000`

2. **Open the frontend:**
   - Navigate to `http://localhost:8000/web/` (served by FastAPI)
   - Or open `web/index.html` directly in browser (will connect to localhost:8000)

3. **Check WebSocket connection:**
   - Open browser DevTools → Network → WS tab
   - Click "Generate" button
   - See WebSocket connection established
   - Monitor messages in real-time

4. **Debug Panel:**
   - The frontend includes a debug panel (bottom of sidebar)
   - Shows WebSocket status, message count, errors, and recent messages

## Error Handling

- **Connection errors:** Frontend displays error message and resets UI
- **Backend errors:** Sent as `error` message type, displayed in UI
- **Kill switch:** Frontend can stop analysis by sending `stop_analysis` action
- **WebSocket disconnection:** Frontend handles close events and resets state

## CORS Configuration

**File: `api/main.py` (lines 485-491)**

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Currently allows all origins for development. In production, specify your frontend URL.

