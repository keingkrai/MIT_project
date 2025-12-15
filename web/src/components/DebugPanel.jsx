import { useState } from 'react'
import { useWebSocket } from '../contexts/WebSocketContext'
import { useAnalysis } from '../contexts/AnalysisContext'

function DebugPanel() {
  const [isExpanded, setIsExpanded] = useState(false)
  const { debugState, connectWebSocket, disconnectWebSocket, checkBackendHealth } = useWebSocket()
  const { teamState, isRunning } = useAnalysis()

  const getStatusIndicatorClass = () => {
    if (debugState.wsConnected) return 'status-indicator connected'
    return 'status-indicator disconnected'
  }

  const getStatusText = () => {
    if (debugState.wsConnected) return 'Connected'
    return 'Disconnected'
  }

  const calculateTeamProgress = (team) => {
    const completed = team.filter((m) => m.status === 'completed').length
    const inProgress = team.filter((m) => m.status === 'in_progress').length
    const pending = team.filter((m) => m.status === 'pending').length
    const total = team.length
    const percentage = Math.round((completed / total) * 100)
    return { completed, inProgress, pending, total, percentage }
  }

  const analystProgress = calculateTeamProgress(teamState.analyst)
  const researchProgress = calculateTeamProgress(teamState.research)
  const traderProgress = calculateTeamProgress(teamState.trader)
  const riskProgress = calculateTeamProgress(teamState.risk)

  const totalAgents = analystProgress.total + researchProgress.total + traderProgress.total + riskProgress.total
  const totalCompleted = analystProgress.completed + researchProgress.completed + traderProgress.completed + riskProgress.completed
  const totalInProgress = analystProgress.inProgress + researchProgress.inProgress + traderProgress.inProgress + riskProgress.inProgress
  const overallProgress = Math.round((totalCompleted / totalAgents) * 100)

  return (
    <div className="debug-section-container">
      <div className="debug-header">
        <div className="debug-title">
          <span>🔍 Debug Panel</span>
          <span className="debug-badge">
            {debugState.wsConnected ? '🟢' : '🔴'} {getStatusText()}
          </span>
        </div>
        <button
          className="debug-toggle-btn"
          onClick={() => setIsExpanded(!isExpanded)}
          aria-label={isExpanded ? 'Collapse debug panel' : 'Expand debug panel'}
        >
          {isExpanded ? '▼' : '▲'}
        </button>
      </div>

      {isExpanded && (
        <div className="debug-content">
          <div className="debug-grid">
            <div className="debug-item">
              <div className="debug-label">WebSocket Status</div>
              <div className="debug-value">
                <span className={getStatusIndicatorClass()}></span>
                {getStatusText()}
              </div>
            </div>
            <div className="debug-item">
              <div className="debug-label">Connection URL</div>
              <div className="debug-value" style={{ fontSize: '0.75rem', wordBreak: 'break-all' }}>
                {debugState.wsUrl || '—'}
              </div>
            </div>
            <div className="debug-item">
              <div className="debug-label">Pipeline Status</div>
              <div className="debug-value">
                {isRunning ? '🟢 Running' : '⚪ Idle'}
              </div>
            </div>
            <div className="debug-item">
              <div className="debug-label">Overall Progress</div>
              <div className="debug-value">
                {overallProgress}% ({totalCompleted}/{totalAgents} completed, {totalInProgress} in progress)
              </div>
            </div>
            <div className="debug-item">
              <div className="debug-label">Messages Received</div>
              <div className="debug-value">{debugState.messageCount}</div>
            </div>
            <div className="debug-item">
              <div className="debug-label">Errors</div>
              <div className="debug-value" style={{ color: debugState.errorCount > 0 ? 'var(--danger)' : 'inherit' }}>
                {debugState.errorCount}
              </div>
            </div>
            <div className="debug-item">
              <div className="debug-label">Last Update</div>
              <div className="debug-value">
                {debugState.lastUpdate ? new Date(debugState.lastUpdate).toLocaleTimeString() : '—'}
              </div>
            </div>
            <div className="debug-item">
              <div className="debug-label">Last Message Type</div>
              <div className="debug-value">{debugState.lastType || '—'}</div>
            </div>
          </div>

          <div className="debug-grid" style={{ marginTop: '16px' }}>
            <div className="debug-item">
              <div className="debug-label">Analyst Team</div>
              <div className="debug-value">
                {analystProgress.percentage}% ({analystProgress.completed}/{analystProgress.total})
                <br />
                <small style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                  {analystProgress.inProgress} in progress, {analystProgress.pending} pending
                </small>
              </div>
            </div>
            <div className="debug-item">
              <div className="debug-label">Research Team</div>
              <div className="debug-value">
                {researchProgress.percentage}% ({researchProgress.completed}/{researchProgress.total})
                <br />
                <small style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                  {researchProgress.inProgress} in progress, {researchProgress.pending} pending
                </small>
              </div>
            </div>
            <div className="debug-item">
              <div className="debug-label">Trader Team</div>
              <div className="debug-value">
                {traderProgress.percentage}% ({traderProgress.completed}/{traderProgress.total})
                <br />
                <small style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                  {traderProgress.inProgress} in progress, {traderProgress.pending} pending
                </small>
              </div>
            </div>
            <div className="debug-item">
              <div className="debug-label">Risk & Portfolio</div>
              <div className="debug-value">
                {riskProgress.percentage}% ({riskProgress.completed}/{riskProgress.total})
                <br />
                <small style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                  {riskProgress.inProgress} in progress, {riskProgress.pending} pending
                </small>
              </div>
            </div>
          </div>

          <div className="debug-log-section">
            <div className="debug-log-header">
              <span>Recent Messages ({debugState.logEntries.length})</span>
              <div className="debug-actions">
                <button
                  className="debug-btn"
                  onClick={() => {
                    disconnectWebSocket()
                    setTimeout(() => {
                      checkBackendHealth()
                      connectWebSocket()
                    }, 500)
                  }}
                >
                  {debugState.wsConnected ? 'Reconnect' : 'Connect'}
                </button>
              </div>
            </div>
            <div className="debug-log">
              {debugState.logEntries.length === 0 ? (
                <div className="debug-log-empty">No messages yet</div>
              ) : (
                debugState.logEntries.slice(-10).map((entry, idx) => {
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
                        {entry.content.substring(0, 150)}
                        {entry.content.length > 150 ? '...' : ''}
                      </span>
                    </div>
                  )
                })
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default DebugPanel


