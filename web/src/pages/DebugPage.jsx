import { useState } from 'react'
import { useWebSocket } from '../contexts/WebSocketContext'

function DebugPage() {
  const { debugState, connectWebSocket, disconnectWebSocket, checkBackendHealth } = useWebSocket()
  const [copyButtonText, setCopyButtonText] = useState('Copy Log')

  const clearLog = () => {
    setDebugState((prev) => ({
      ...prev,
      logEntries: [],
      messageCount: 0,
      errorCount: 0,
    }))
  }

  const copyLog = async () => {
    const logText = debugState.logEntries
      .map((entry) => `[${entry.time}] [${entry.type}] ${entry.content}`)
      .join('\n')
    try {
      await navigator.clipboard.writeText(logText)
      setCopyButtonText('Copied!')
      setTimeout(() => setCopyButtonText('Copy Log'), 2000)
    } catch (error) {
      console.error('Failed to copy log:', error)
    }
  }

  const getStatusIndicatorClass = () => {
    if (debugState.wsConnected) return 'status-indicator connected'
    return 'status-indicator disconnected'
  }

  const getStatusText = () => {
    if (debugState.wsConnected) return 'Connected'
    return 'Disconnected'
  }

  const handleReconnect = () => {
    disconnectWebSocket()
    setTimeout(() => {
      checkBackendHealth()
      connectWebSocket()
    }, 500)
  }

  return (
    <div className="page-content">
      <header className="main-header">
        <div>
          <p className="eyebrow">System diagnostics</p>
          <h1>Debug Panel</h1>
        </div>
      </header>

      <section className="debug-page-content">
        <div className="debug-section">
          <div className="debug-label">WebSocket Status</div>
          <div className="debug-value" id="debug-ws-status-page">
            <span className={getStatusIndicatorClass()}></span>
            <span>{getStatusText()}</span>
          </div>
        </div>
        <div className="debug-section">
          <div className="debug-label">Connection URL</div>
          <div className="debug-value" id="debug-ws-url-page">{debugState.wsUrl || '—'}</div>
        </div>
        <div className="debug-section">
          <div className="debug-label">Messages Received</div>
          <div className="debug-value" id="debug-msg-count-page">{debugState.messageCount}</div>
        </div>
        <div className="debug-section">
          <div className="debug-label">Last Update</div>
          <div className="debug-value" id="debug-last-update-page">
            {debugState.lastUpdate ? new Date(debugState.lastUpdate).toLocaleTimeString() : '—'}
          </div>
        </div>
        <div className="debug-section">
          <div className="debug-label">Last Message Type</div>
          <div className="debug-value" id="debug-last-type-page">{debugState.lastType || '—'}</div>
        </div>
        <div className="debug-section">
          <div className="debug-label">Errors</div>
          <div className="debug-value" id="debug-error-count-page">{debugState.errorCount}</div>
        </div>
        <div className="debug-section full-width">
          <div className="debug-label">Recent Messages</div>
          <div className="debug-log" id="debug-log-page">
            {debugState.logEntries.length === 0 ? (
              <div className="debug-log-empty">No messages yet</div>
            ) : (
              debugState.logEntries.slice(-debugState.maxLogEntries).map((entry, idx) => {
                const entryClass =
                  entry.type === 'error'
                    ? 'error'
                    : entry.type === 'warning'
                    ? 'warning'
                    : ''
                return (
                  <div key={idx} className={`debug-log-entry ${entryClass}`}>
                    <span className="debug-log-entry-time">{entry.time}</span>
                    <span className="debug-log-entry-type">[{entry.type}]</span>
                    <span className="debug-log-entry-content">
                      {entry.content.substring(0, 100)}
                      {entry.content.length > 100 ? '...' : ''}
                    </span>
                  </div>
                )
              })
            )}
          </div>
        </div>
        <div className="debug-actions">
          <button className="debug-btn" onClick={clearLog}>
            Clear Log
          </button>
          <button className="debug-btn" onClick={copyLog}>
            {copyButtonText}
          </button>
          <button className="debug-btn" onClick={handleReconnect}>
            {debugState.wsConnected ? 'Reconnect' : 'Connect'}
          </button>
        </div>
      </section>
    </div>
  )
}

export default DebugPage

