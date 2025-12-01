"""
Start the FastAPI backend server for TradingAgents web interface.
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="localhost",
        port=8000,
        reload=True,  # Enable auto-reload during development
        log_level="info"
    )

