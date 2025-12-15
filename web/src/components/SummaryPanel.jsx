function SummaryPanel({ ticker, analysisDate, recommendation }) {
  // Normalize recommendation for variant detection
  const normalized = recommendation ? recommendation.toLowerCase() : ''
  let variant = 'neutral'
  
  if (normalized.includes('buy')) {
    variant = 'buy'
  } else if (normalized.includes('sell')) {
    variant = 'sell'
  } else if (normalized.includes('reduce') || normalized.includes('monitor')) {
    variant = 'reduce'
  } else if (normalized.includes('hold')) {
    variant = 'neutral'
  }

  // Format recommendation display text
  const displayRecommendation = recommendation && recommendation !== 'Awaiting run' 
    ? recommendation 
    : 'Awaiting run'

  return (
    <section className="summary-panel">
      <div>
        <p>Summary</p>
        <div className="summary-grid">
          <div>
            <span>Symbol</span>
            <strong>{ticker || '—'}</strong>
          </div>
          <div>
            <span>Date</span>
            <strong>{analysisDate || '—'}</strong>
          </div>
        </div>
      </div>
      <div className="recommendation" data-variant={variant}>
        <span>Recommendation: <strong>{displayRecommendation}</strong></span>
      </div>
    </section>
  )
}

export default SummaryPanel

