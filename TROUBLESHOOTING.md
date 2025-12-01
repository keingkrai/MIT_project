# FastAPI Backend Troubleshooting Guide

## Common Issues and Solutions

### 1. "Module not found" or Import Errors

**Error**: `ModuleNotFoundError: No module named 'api'` or similar

**Solution**:
- Make sure you're running from the project root directory (`MIT_project-main`)
- Try: `python -m api.main` instead of `python api/main.py`
- Or use: `python start_api.py`

### 2. Server Won't Start

**Error**: Port 8000 already in use

**Solution**:
```bash
# Windows: Find and kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or change the port in start_api.py
uvicorn.run("api.main:app", host="0.0.0.0", port=8001, reload=True)
```

### 3. WebSocket Connection Failed

**Error**: `WebSocket connection failed` in browser console

**Solutions**:
1. **Check if server is running**:
   ```bash
   python start_api.py
   ```
   You should see: `INFO:     Uvicorn running on http://0.0.0.0:8000`

2. **Check WebSocket URL in browser**:
   - Open browser console (F12)
   - Look for WebSocket connection attempts
   - Should be: `ws://localhost:8000/ws` (or `wss://` for HTTPS)

3. **Test WebSocket manually**:
   ```python
   import asyncio
   import websockets
   import json
   
   async def test():
       uri = "ws://localhost:8000/ws"
       async with websockets.connect(uri) as websocket:
           await websocket.send(json.dumps({"action": "ping"}))
           response = await websocket.recv()
           print(json.loads(response))
   
   asyncio.run(test())
   ```

### 4. Static Files Not Loading

**Error**: 404 errors for CSS/JS files

**Solution**:
- Check that `web/` directory exists in project root
- Verify paths in `api/main.py`:
  ```python
  PROJECT_ROOT = Path(__file__).parent.parent
  WEB_DIR = PROJECT_ROOT / "web"
  ```
- Try accessing: `http://localhost:8000/web/index.html`

### 5. Analysis Not Starting

**Error**: No response when clicking "Generate"

**Solutions**:
1. **Check browser console** for JavaScript errors
2. **Check API logs** for backend errors
3. **Verify API keys** are set in `.env`:
   ```bash
   OPENAI_API_KEY=your_key
   ALPHA_VANTAGE_API_KEY=your_key
   ```
4. **Test API endpoints**:
   ```bash
   python test_api.py
   ```

### 6. "TradingAgents modules not found"

**Error**: `ImportError: cannot import name 'TradingAgentsGraph'`

**Solution**:
- Make sure you're in the project root
- Install dependencies: `pip install -r requirements.txt`
- Check Python path: `python -c "import sys; print(sys.path)"`

### 7. CORS Errors

**Error**: `Access-Control-Allow-Origin` errors in browser

**Solution**:
- CORS is already configured to allow all origins (`allow_origins=["*"]`)
- If still having issues, check `api/main.py` CORS configuration
- Make sure you're accessing via `http://localhost:8000` not `file://`

### 8. Results Directory Not Found

**Error**: `FileNotFoundError` when saving reports

**Solution**:
- Check `tradingagents/default_config.py` for `results_dir` setting
- Default is `./results` (relative to project root)
- The API will create directories automatically, but check permissions

## Testing the API

### Quick Test
```bash
# Start the server
python start_api.py

# In another terminal, test endpoints
python test_api.py

# Or manually:
curl http://localhost:8000/api/health
curl http://localhost:8000/api/test
```

### WebSocket Test
```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        # Send ping
        await websocket.send(json.dumps({"action": "ping"}))
        response = await websocket.recv()
        print("Ping response:", json.loads(response))
        
        # Send analysis request (will take time)
        request = {
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
        }
        await websocket.send(json.dumps(request))
        
        # Listen for updates
        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                print(f"[{data['type']}] {data.get('data', {})}")
                if data['type'] == 'complete' or data['type'] == 'error':
                    break
            except websockets.exceptions.ConnectionClosed:
                break

asyncio.run(test_websocket())
```

## Debug Mode

Enable verbose logging:
```python
# In api/main.py, change:
logging.basicConfig(level=logging.DEBUG)
```

Or set environment variable:
```bash
export PYTHONUNBUFFERED=1
python start_api.py
```

## Getting Help

1. Check server logs for error messages
2. Check browser console (F12) for frontend errors
3. Test individual components:
   - API health: `curl http://localhost:8000/api/health`
   - WebSocket: Use test script above
   - TradingAgents: `python -m cli.main analyze`

## Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `Connection refused` | Server not running | Start with `python start_api.py` |
| `ModuleNotFoundError` | Wrong directory | Run from project root |
| `Port already in use` | Another process on port 8000 | Kill process or change port |
| `WebSocket closed` | Connection lost | Check network/server logs |
| `Invalid request` | Missing fields | Check request format in browser console |

