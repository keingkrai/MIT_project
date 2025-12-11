# TradingAgents Web Application

A React + Vite application for the TradingAgents LLM Trading Lab.

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

```bash
npm install
```

### Development

Start the development server:

```bash
npm run dev
```

The application will be available at `http://localhost:3000`

### Build

Build for production:

```bash
npm run build
```

This creates a `dist/` directory with production-ready files. FastAPI will automatically serve from `dist/` when it exists.

### Preview

Preview the production build:

```bash
npm run preview
```

## Production Deployment

1. **Build the React app:**
   ```bash
   cd web
   npm run build
   ```

2. **Start FastAPI server:**
   ```bash
   python start_api.py
   ```

3. **Access the application:**
   - Open your browser and go to: `http://localhost:8000/web/`
   - Or directly: `http://localhost:8000` (redirects to `/web/`)

FastAPI will automatically detect and serve from `web/dist/` if it exists, otherwise it falls back to `web/` directory.

## Project Structure

```
web/
├── src/
│   ├── components/     # React components
│   ├── pages/         # Page components
│   ├── App.jsx        # Main app component
│   ├── main.jsx       # Entry point
│   └── styles.css     # Global styles
├── index.html         # HTML template
├── package.json       # Dependencies
└── vite.config.js     # Vite configuration
```

## Features

- Generate trading analysis reports
- Real-time WebSocket connection to backend
- Team progress tracking
- Report viewing and export (PDF)
- Debug panel for system diagnostics

## WebSocket Connection

The WebSocket connection is automatically configured:
- **Development**: Uses proxy `/ws` → `ws://localhost:8000/ws` (via Vite dev server)
- **Production**: Connects to `/ws` on the same hostname (FastAPI serves WebSocket at root level)

## Legacy Version

A vanilla JavaScript version is also available at `/legacy` endpoint:
- **Legacy URL**: `http://localhost:8000/legacy`
- Uses `script.js` for all functionality
- Connects to FastAPI WebSocket at `ws://localhost:8000/ws`
- Same functionality as React version, but using vanilla JS

## Development vs Production

### Development Mode
- Vite dev server runs on `http://localhost:3000`
- FastAPI backend runs on `http://localhost:8000`
- WebSocket connections are proxied through Vite dev server

### Production Mode
- Build React app: `npm run build` (creates `dist/` folder)
- FastAPI serves both the React app and WebSocket endpoint
- Access at `http://localhost:8000/web/`
- WebSocket connects to `ws://localhost:8000/ws`

