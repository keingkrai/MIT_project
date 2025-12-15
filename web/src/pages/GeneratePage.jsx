import { useAnalysis } from '../contexts/AnalysisContext'
import StepCard from '../components/StepCard'
import TeamCard from '../components/TeamCard'
import ReportPanel from '../components/ReportPanel'
import SummaryPanel from '../components/SummaryPanel'
import DebugPanel from '../components/DebugPanel'
import StockSearchInput from '../components/StockSearchInput'

function toISODate() {
  return new Date().toISOString().split('T')[0]
}

function GeneratePage() {
  const {
    ticker,
    setTicker,
    analysisDate,
    setAnalysisDate,
    reportLength,
    setReportLength,
    isRunning,
    teamState,
    reportSections,
    reportView,
    setReportView,
    recommendation,
    connectionError,
    runPipeline,
    stopPipeline,
  } = useAnalysis()

  return (
    <div className="page-content">
      <header className="main-header">
        <div>
          <p className="eyebrow">Trading workflow</p>
          <h1>Generate</h1>
        </div>
        <div className="header-controls">
          <button
            className={`primary ${isRunning ? 'stop' : ''}`}
            onClick={runPipeline}
            disabled={false}
          >
            {isRunning ? 'Stop' : 'Generate'}
          </button>
        </div>
      </header>

      <section className="step-grid">
        <StepCard
          step={1}
          title="Ticker Symbol"
          children={
            <label className="input">
              <span>Search stocks (ex. SPY, AAPL, NVDA)</span>
              <StockSearchInput
                value={ticker}
                onChange={(value) => setTicker(value)}
                placeholder="SPY"
              />
            </label>
          }
        />

        <StepCard
          step={2}
          title="Analysis Date"
          children={
            <label className="input">
              <span>YYYY-MM-DD</span>
              <input
                type="date"
                value={analysisDate}
                onChange={(e) => setAnalysisDate(e.target.value || toISODate())}
              />
            </label>
          }
        />

        <StepCard
          step={3}
          title="Report Length"
          children={
            <div className="report-length-options">
              <button
                className={`report-length-option ${reportLength === 'short' ? 'active' : ''}`}
                onClick={() => setReportLength('short')}
              >
                <strong>Summary Report</strong>
                <span>Concise summary with key point</span>
              </button>
              <button
                className={`report-length-option ${reportLength === 'long' ? 'active' : ''}`}
                onClick={() => setReportLength('long')}
              >
                <strong>Full Report</strong>
                <span>Comprehensive detailed analysis</span>
              </button>
            </div>
          }
        />
      </section>

      {connectionError && (
        <section className="connection-error-section">
          <p>⚠️ Connection Error</p>
          <p>{connectionError}</p>
          <p>
            <strong>To fix this:</strong>
            <br />
            1. Make sure FastAPI backend is running: <code>python start_api.py</code>
            <br />
            2. Check that FastAPI is running on port 8000
            <br />
            3. Verify the WebSocket endpoint is accessible at <code>ws://localhost:8000/ws</code>
          </p>
        </section>
      )}

      <DebugPanel />

      <section className="teams-grid">
        <TeamCard teamKey="analyst" teamState={teamState.analyst} title="Analyst team" subtitle="Market • News • Social • Fundamentals" />
        <TeamCard teamKey="research" teamState={teamState.research} title="Research team" subtitle="Bull • Bear • Manager" />
        <TeamCard teamKey="trader" teamState={teamState.trader} title="Trader team" subtitle="Execution" />
        <TeamCard teamKey="risk" teamState={teamState.risk} title="Risk team" subtitle="Risky • Neutral • Safe" />
        <TeamCard teamKey="portfolio" teamState={teamState.portfolio} title="Portfolio team" subtitle="Manager" />
      </section>

      <ReportPanel
        reportSections={reportSections}
        reportView={reportView}
        setReportView={setReportView}
        ticker={ticker}
        analysisDate={analysisDate}
        reportLength={reportLength}
        teamState={teamState}
      />

      <SummaryPanel ticker={ticker} analysisDate={analysisDate} recommendation={recommendation} />
    </div>
  )
}

export default GeneratePage

