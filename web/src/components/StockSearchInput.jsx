import { useState, useRef, useEffect } from 'react'

// Popular stock symbols with company names
const POPULAR_STOCKS = [
  { symbol: 'SPY', name: 'SPDR S&P 500 ETF Trust' },
  { symbol: 'AAPL', name: 'Apple Inc.' },
  { symbol: 'MSFT', name: 'Microsoft Corporation' },
  { symbol: 'NVDA', name: 'NVIDIA Corporation' },
  { symbol: 'GOOGL', name: 'Alphabet Inc. Class A' },
  { symbol: 'AMZN', name: 'Amazon.com Inc.' },
  { symbol: 'META', name: 'Meta Platforms Inc.' },
  { symbol: 'TSLA', name: 'Tesla Inc.' },
  { symbol: 'BRK.B', name: 'Berkshire Hathaway Inc. Class B' },
  { symbol: 'UNH', name: 'UnitedHealth Group Inc.' },
  { symbol: 'JNJ', name: 'Johnson & Johnson' },
  { symbol: 'V', name: 'Visa Inc.' },
  { symbol: 'WMT', name: 'Walmart Inc.' },
  { symbol: 'JPM', name: 'JPMorgan Chase & Co.' },
  { symbol: 'MA', name: 'Mastercard Inc.' },
  { symbol: 'PG', name: 'Procter & Gamble Co.' },
  { symbol: 'HD', name: 'The Home Depot Inc.' },
  { symbol: 'DIS', name: 'The Walt Disney Company' },
  { symbol: 'BAC', name: 'Bank of America Corp.' },
  { symbol: 'AVGO', name: 'Broadcom Inc.' },
  { symbol: 'XOM', name: 'Exxon Mobil Corporation' },
  { symbol: 'COST', name: 'Costco Wholesale Corporation' },
  { symbol: 'PFE', name: 'Pfizer Inc.' },
  { symbol: 'ABBV', name: 'AbbVie Inc.' },
  { symbol: 'CVX', name: 'Chevron Corporation' },
  { symbol: 'CSCO', name: 'Cisco Systems Inc.' },
  { symbol: 'ADBE', name: 'Adobe Inc.' },
  { symbol: 'NFLX', name: 'Netflix Inc.' },
  { symbol: 'CMCSA', name: 'Comcast Corporation' },
  { symbol: 'PEP', name: 'PepsiCo Inc.' },
  { symbol: 'TMO', name: 'Thermo Fisher Scientific Inc.' },
  { symbol: 'WFC', name: 'Wells Fargo & Company' },
  { symbol: 'INTC', name: 'Intel Corporation' },
  { symbol: 'TXN', name: 'Texas Instruments Incorporated' },
  { symbol: 'QCOM', name: 'QUALCOMM Incorporated' },
  { symbol: 'COIN', name: 'Coinbase Global Inc.' },
  { symbol: 'AMD', name: 'Advanced Micro Devices Inc.' },
  { symbol: 'NKE', name: 'Nike Inc.' },
  { symbol: 'SBUX', name: 'Starbucks Corporation' },
  { symbol: 'MU', name: 'Micron Technology Inc.' },
  { symbol: 'AMAT', name: 'Applied Materials Inc.' },
  { symbol: 'LRCX', name: 'Lam Research Corporation' },
  { symbol: 'ASML', name: 'ASML Holding N.V.' },
  { symbol: 'TSM', name: 'Taiwan Semiconductor Manufacturing' },
  { symbol: 'BABA', name: 'Alibaba Group Holding Limited' },
  { symbol: 'NIO', name: 'NIO Inc.' },
  { symbol: 'PLTR', name: 'Palantir Technologies Inc.' },
  { symbol: 'RIVN', name: 'Rivian Automotive Inc.' },
  { symbol: 'LCID', name: 'Lucid Group Inc.' },
  { symbol: 'F', name: 'Ford Motor Company' },
  { symbol: 'GM', name: 'General Motors Company' },
  { symbol: 'RBLX', name: 'Roblox Corporation' },
  { symbol: 'SOFI', name: 'SoFi Technologies Inc.' },
  { symbol: 'HOOD', name: 'Robinhood Markets Inc.' },
  { symbol: 'QQQ', name: 'Invesco QQQ Trust' },
  { symbol: 'DIA', name: 'SPDR Dow Jones Industrial Average' },
  { symbol: 'IWM', name: 'iShares Russell 2000 ETF' },
  { symbol: 'VTI', name: 'Vanguard Total Stock Market ETF' },
  { symbol: 'ARKK', name: 'ARK Innovation ETF' },
]

function StockSearchInput({ value, onChange, placeholder = 'SPY' }) {
  const [searchTerm, setSearchTerm] = useState('')
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [filteredStocks, setFilteredStocks] = useState([])
  const inputRef = useRef(null)
  const suggestionsRef = useRef(null)

  // Filter stocks based on search term
  useEffect(() => {
    if (searchTerm.trim() === '') {
      setFilteredStocks(POPULAR_STOCKS.slice(0, 10)) // Show top 10 when empty
    } else {
      const term = searchTerm.toUpperCase()
      const filtered = POPULAR_STOCKS.filter(
        (stock) =>
          stock.symbol.includes(term) ||
          stock.name.toUpperCase().includes(term)
      )
      setFilteredStocks(filtered.slice(0, 15)) // Limit to 15 results
    }
  }, [searchTerm])

  // Sync searchTerm with value prop
  useEffect(() => {
    setSearchTerm(value || '')
  }, [value])

  // Handle input change
  const handleInputChange = (e) => {
    const newValue = e.target.value.trim().toUpperCase()
    setSearchTerm(newValue)
    setShowSuggestions(true)
    // Allow empty value - don't force default
    onChange(newValue)
  }

  // Handle stock selection
  const handleSelectStock = (stock) => {
    setSearchTerm(stock.symbol)
    setShowSuggestions(false)
    onChange(stock.symbol)
    inputRef.current?.blur()
  }

  // Handle input focus
  const handleFocus = () => {
    setShowSuggestions(true)
  }

  // Handle input blur (with delay to allow click on suggestions)
  const handleBlur = () => {
    setTimeout(() => {
      setShowSuggestions(false)
    }, 200)
  }

  // Handle keyboard navigation
  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      setShowSuggestions(false)
      inputRef.current?.blur()
    } else if (e.key === 'Enter' && filteredStocks.length > 0) {
      e.preventDefault()
      handleSelectStock(filteredStocks[0])
    }
  }

  return (
    <div className="stock-search-container">
      <input
        ref={inputRef}
        type="text"
        value={searchTerm}
        onChange={handleInputChange}
        onFocus={handleFocus}
        onBlur={handleBlur}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        autoComplete="off"
        className="stock-search-input"
      />
      {showSuggestions && filteredStocks.length > 0 && (
        <div ref={suggestionsRef} className="stock-suggestions">
          {filteredStocks.map((stock) => (
            <div
              key={stock.symbol}
              className="stock-suggestion-item"
              onClick={() => handleSelectStock(stock)}
              onMouseDown={(e) => e.preventDefault()} // Prevent blur before click
            >
              <span className="stock-symbol">{stock.symbol}</span>
              <span className="stock-name">{stock.name}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default StockSearchInput

