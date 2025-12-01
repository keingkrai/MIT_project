# TradingAgents FastAPI Backend

This document explains how to use the FastAPI backend to connect the web interface to the TradingAgents CLI.

## Overview

The FastAPI backend (`api/main.py`) provides:
- **WebSocket support** for real-time updates during analysis
- **REST API** endpoints for health checks
- **Static file serving** for the web interface
- **CORS configuration** for cross-origin requests

## Setup

### 1. Install Dependencies

All required dependencies are already in `requirements.txt`. FastAPI, uvicorn, and websockets are included.

### 2. Configure Environment Variables

Make sure you have a `.env` file in the project root with your API keys:

```bash
OPENAI_API_KEY=your_openai_api_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key
# Or other provider keys as needed
```

## Running the Backend

### Option 1: Using the startup script

```bash
python start_api.py
```

### Option 2: Using uvicorn directly

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Option 3: Using Python module

```bash
python -m api.main
```

The server will start on `http://localhost:8000`

## Accessing the Web Interface

Once the backend is running, you can access the web interface at:

- **Main page**: `http://localhost:8000/` or `http://localhost:8000/web/`
- **WebSocket endpoint**: `ws://localhost:8000/ws`
- **Health check**: `http://localhost:8000/api/health`

## How It Works

### WebSocket Communication

1. **Client connects** to `ws://localhost:8000/ws`
2. **Client sends** an analysis request:
   ```json
   {
     "action": "start_analysis",
     "request": {
       "ticker": "SPY",
       "analysis_date": "2025-01-15",
       "analysts": ["market", "social", "news", "fundamentals"],
       "research_depth": 3,
       "llm_provider": "google",
       "backend_url": "https://generativelanguage.googleapis.com/v1",
       "shallow_thinker": "gemini-2.0-flash-lite",
       "deep_thinker": "gemini-2.0-flash-lite"
     }
   }
   ```

3. **Server streams** real-time updates:
   - `status`: Agent status updates (pending → in_progress → completed)
   - `message`: LLM reasoning messages
   - `tool_call`: Tool execution notifications
   - `report`: Report section updates
   - `complete`: Final analysis completion with decision
   - `error`: Error messages

### Message Types

#### Status Update
```json
{
  "type": "status",
  "data": {
    "agents": {
      "Market Analyst": "completed",
      "Social Analyst": "in_progress",
      ...
    }
  }
}
```

#### Report Update
```json
{
  "type": "report",
  "data": {
    "section": "market_report",
    "label": "Market Analysis",
    "content": "Markdown content..."
  }
}
```

#### Completion
```json
{
  "type": "complete",
  "data": {
    "decision": "BUY",
    "final_state": {
      "market_report": "...",
      "final_trade_decision": "..."
    }
  }
}
```

## File Structure

```
MIT_project-main/
├── api/
│   ├── __init__.py
│   └── main.py          # FastAPI backend
├── web/
│   ├── index.html       # Frontend HTML
│   ├── script.js        # Frontend JavaScript (WebSocket client)
│   └── styles.css       # Frontend styles
├── start_api.py         # Startup script
└── requirements.txt     # Dependencies
```

## Troubleshooting

### WebSocket Connection Failed

- Make sure the FastAPI backend is running on port 8000
- Check browser console for connection errors
- Verify CORS settings if accessing from a different origin

### Analysis Not Starting

- Check that all required fields are provided in the request
- Verify API keys are set in `.env`
- Check backend logs for error messages

### Reports Not Updating

- Ensure WebSocket connection is active
- Check browser console for incoming messages
- Verify the backend is processing chunks correctly

## Development

### Adding New Features

1. **New WebSocket message types**: Add new cases in `run_analysis_stream()`
2. **New API endpoints**: Add routes to `app` in `api/main.py`
3. **Frontend updates**: Modify `web/script.js` to handle new message types

### Testing

Test the WebSocket connection:
```python
import asyncio
import websockets
import json

async def test():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps({
            "action": "start_analysis",
            "request": {
                "ticker": "SPY",
                "analysis_date": "2025-01-15",
                "analysts": ["market"],
                "research_depth": 1,
                "llm_provider": "google",
                "backend_url": "https://generativelanguage.googleapis.com/v1",
                "shallow_thinker": "gemini-2.0-flash-lite",
                "deep_thinker": "gemini-2.0-flash-lite"
            }
        }))
        while True:
            message = await websocket.recv()
            print(json.loads(message))

asyncio.run(test())
```

## Production Deployment

For production:
1. Set `allow_origins` in CORS middleware to your frontend domain
2. Use a production ASGI server like Gunicorn with Uvicorn workers
3. Set up proper logging and error handling
4. Configure HTTPS/WSS for secure WebSocket connections
5. Add authentication/authorization if needed

