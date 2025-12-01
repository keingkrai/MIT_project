# Web Interface Setup Guide

## Quick Start

1. **Start the FastAPI server:**
   ```bash
   python start_api.py
   ```

2. **Access the web interface:**
   - Open your browser and go to: `http://localhost:8000`
   - Or directly: `http://localhost:8000/web/`
   - The root URL (`/`) will automatically redirect to `/web/`

## How It Works

### FastAPI Configuration

The FastAPI server (`api/main.py`) is configured to:

1. **Serve static files** from the `web/` directory at `/web/`
   - This includes `index.html`, `styles.css`, `script.js`, and other assets
   - Uses FastAPI's `StaticFiles` with `html=True` to serve `index.html` automatically

2. **WebSocket endpoint** at `/ws`
   - The frontend connects to this for real-time analysis updates
   - Handles analysis requests and streams results back

3. **Root redirect** (`/`)
   - Automatically redirects to `/web/` for convenience

### File Structure

```
MIT_project-main/
├── api/
│   └── main.py          # FastAPI server
├── web/
│   ├── index.html       # Main web interface
│   ├── styles.css      # Styles
│   └── script.js        # Frontend logic (WebSocket client)
└── start_api.py         # Server startup script
```

### WebSocket Connection

The frontend (`web/script.js`) automatically detects the WebSocket URL:
- If served from FastAPI: Uses `ws://localhost:8000/ws` (or `wss://` for HTTPS)
- If opened as file: Falls back to `ws://localhost:8000/ws`

## Troubleshooting

### Issue: "Web interface not found"
- Check that the `web/` directory exists in the project root
- Verify `WEB_DIR` path in `api/main.py` is correct

### Issue: CSS/JS files not loading
- Ensure you're accessing via `/web/` path (not root `/`)
- Check browser console for 404 errors
- Verify static files exist in `web/` directory

### Issue: WebSocket connection fails
- Ensure FastAPI server is running on port 8000
- Check that `/ws` endpoint is accessible
- Look at browser console for WebSocket errors

## API Endpoints

- `GET /` - Redirects to `/web/`
- `GET /web/` - Serves the web interface
- `GET /web/*` - Serves static files (CSS, JS, etc.)
- `WS /ws` - WebSocket endpoint for analysis
- `GET /api/health` - Health check endpoint
- `GET /api/test` - Test endpoint

## Development

The server runs with auto-reload enabled (`reload=True`), so changes to Python files will automatically restart the server.

For frontend changes, refresh your browser to see updates.




