import { createContext, useContext, useState, useCallback, useRef, useEffect } from 'react'

const AnalysisContext = createContext(null)

const teamTemplate = {
  analyst: [
    { name: 'Market Analyst', status: 'pending' },
    { name: 'Social Media Analyst', status: 'pending' },
    { name: 'News Analyst', status: 'pending' },
    { name: 'Fundamentals Analyst', status: 'pending' },
  ],
  research: [
    { name: 'Bull Research', status: 'pending' },
    { name: 'Bear Research', status: 'pending' },
    { name: 'Research Manager', status: 'pending' },
  ],
  trader: [{ name: 'Trader', status: 'pending' }],
  risk: [
    { name: 'Risk Analyst', status: 'pending' },
    { name: 'Neutral Analyst', status: 'pending' },
    { name: 'Safe Analyst', status: 'pending' },
  ],
  portfolio: [
    { name: 'Portfolio Manager', status: 'pending' },
  ],
}

const agentToTeamMap = {
  'Market Analyst': ['analyst', 'Market Analyst'],
  'Social Analyst': ['analyst', 'Social Media Analyst'],
  'News Analyst': ['analyst', 'News Analyst'],
  'Fundamentals Analyst': ['analyst', 'Fundamentals Analyst'],
  'Bull Researcher': ['research', 'Bull Research'],
  'Bear Researcher': ['research', 'Bear Research'],
  'Research Manager': ['research', 'Research Manager'],
  'Trader': ['trader', 'Trader'],
  'Risky Analyst': ['risk', 'Risk Analyst'],
  'Neutral Analyst': ['risk', 'Neutral Analyst'],
  'Safe Analyst': ['risk', 'Safe Analyst'],
  'Portfolio Manager': ['portfolio', 'Portfolio Manager'],
}

function toISODate() {
  return new Date().toISOString().split('T')[0]
}

function extractDecision(markdownText) {
  if (!markdownText || typeof markdownText !== 'string') return null
  
  // Look for FINAL TRANSACTION PROPOSAL pattern first
  const proposalMatch = markdownText.match(/FINAL TRANSACTION PROPOSAL:\s*\*\*(BUY|SELL|HOLD|REDUCE|MONITOR|RE-EVALUATE)\*\*/i)
  if (proposalMatch) {
    return proposalMatch[1].toUpperCase()
  }
  
  // Look for standalone decision words
  const match = markdownText.match(/\b(BUY|SELL|HOLD|REDUCE|MONITOR|RE-EVALUATE)\b/i)
  return match ? match[1].toUpperCase() : null
}

export function AnalysisProvider({ children }) {
  const [ticker, setTicker] = useState('SPY')
  const [analysisDate, setAnalysisDate] = useState(toISODate())
  const [headerDate, setHeaderDate] = useState(toISODate())
  const [reportLength, setReportLength] = useState('long')
  const [isRunning, setIsRunning] = useState(false)
  const [teamState, setTeamState] = useState(teamTemplate)
  const [reportSections, setReportSections] = useState([])
  const [reportView, setReportView] = useState('long')
  const [recommendation, setRecommendation] = useState('Awaiting run')
  const [connectionError, setConnectionError] = useState(null)
  const wsConnectionRef = useRef(null)
  const shouldStopRef = useRef(false)
  const keepAliveIntervalRef = useRef(null)

  // Sync dates on mount
  useEffect(() => {
    const today = toISODate()
    setAnalysisDate(today)
    setHeaderDate(today)
  }, [])

  useEffect(() => {
    setHeaderDate(analysisDate)
  }, [analysisDate])

  // Cleanup keepalive interval on unmount
  useEffect(() => {
    return () => {
      if (keepAliveIntervalRef.current) {
        clearInterval(keepAliveIntervalRef.current)
        keepAliveIntervalRef.current = null
      }
    }
  }, [])

  const updateAgentStatus = useCallback((teamKey, agentName, nextStatus) => {
    setTeamState((prev) => {
      const newState = { ...prev }
      const members = [...newState[teamKey]]
      const member = members.find((item) => item.name === agentName)
      if (member) {
        member.status = nextStatus
        newState[teamKey] = members
      }
      return newState
    })
  }, [])

  const stopPipeline = useCallback(() => {
    shouldStopRef.current = true

    // Clear keepalive interval
    if (keepAliveIntervalRef.current) {
      clearInterval(keepAliveIntervalRef.current)
      keepAliveIntervalRef.current = null
    }

    if (wsConnectionRef.current && wsConnectionRef.current.readyState === WebSocket.OPEN) {
      try {
        wsConnectionRef.current.send(JSON.stringify({ action: 'stop_analysis' }))
      } catch (e) {
        console.log('Could not send stop signal:', e)
      }
    }

    if (wsConnectionRef.current) {
      try {
        wsConnectionRef.current.onmessage = null
        wsConnectionRef.current.onerror = null
        wsConnectionRef.current.onclose = null
        wsConnectionRef.current.close()
      } catch (e) {
        console.log('Error closing connection:', e)
      }
      wsConnectionRef.current = null
    }

    setTeamState(JSON.parse(JSON.stringify(teamTemplate)))
    setIsRunning(false)
    shouldStopRef.current = false
    setRecommendation('Awaiting run')
    setReportSections([])
  }, [])

  const runPipeline = useCallback(() => {
    if (isRunning) {
      stopPipeline()
      return
    }

    shouldStopRef.current = false
    setIsRunning(true)
    setTeamState(JSON.parse(JSON.stringify(teamTemplate)))
    setReportSections([])
    setRecommendation('Awaiting run')
    setConnectionError(null)

    // Determine WebSocket URL
    let wsUrl
    const isDevelopment = import.meta.env.DEV
    const isFileProtocol = window.location.protocol === 'file:'

    if (isFileProtocol || window.location.hostname === '') {
      wsUrl = 'ws://localhost:8000/ws'
    } else if (isDevelopment) {
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      wsUrl = `${wsProtocol}//${window.location.host}/ws`
    } else {
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsHost = window.location.hostname
      const wsPort = window.location.port || (window.location.protocol === 'https:' ? '443' : '8000')
      wsUrl = `${wsProtocol}//${wsHost}:${wsPort}/ws`
    }

    console.log(`Attempting to connect to WebSocket: ${wsUrl}`)

    try {
      const ws = new WebSocket(wsUrl)
      wsConnectionRef.current = ws

      const connectionTimeout = setTimeout(() => {
        if (ws.readyState === WebSocket.CONNECTING) {
          console.error('WebSocket connection timeout')
          ws.close()
          const errorMsg = `Connection timeout. Could not connect to ${wsUrl}. Make sure FastAPI backend is running on port 8000.`
          setConnectionError(errorMsg)
          setIsRunning(false)
          shouldStopRef.current = false
          wsConnectionRef.current = null
          setRecommendation('Connection timeout')
        }
      }, 5000)

      ws.onopen = () => {
        clearTimeout(connectionTimeout)
        console.log('WebSocket connected successfully!')
        setConnectionError(null)
        
        // Set up keepalive ping every 30 seconds to keep connection alive
        keepAliveIntervalRef.current = setInterval(() => {
          if (wsConnectionRef.current && wsConnectionRef.current.readyState === WebSocket.OPEN) {
            try {
              wsConnectionRef.current.send(JSON.stringify({ action: 'ping' }))
            } catch (e) {
              console.log('Keepalive ping failed:', e)
            }
          }
        }, 30000)
        
        // Validate ticker before sending request
        const validTicker = ticker && ticker.trim() ? ticker.trim().toUpperCase() : null
        if (!validTicker) {
          alert('Please enter a valid ticker symbol')
          setIsRunning(false)
          return
        }

        const request = {
          action: 'start_analysis',
          request: {
            ticker: validTicker,
            analysis_date: analysisDate,
            report_length: reportLength,
            analysts: ['market', 'social', 'news', 'fundamentals'],
            research_depth: 3,
            llm_provider: 'google',
            backend_url: 'https://generativelanguage.googleapis.com/v1',
            shallow_thinker: 'gemini-2.0-flash-lite',
            deep_thinker: 'gemini-2.0-flash-lite',
          },
        }
        console.log('Sending analysis request:', request)
        ws.send(JSON.stringify(request))
      }

      ws.onmessage = (event) => {
        if (shouldStopRef.current) return

        const message = JSON.parse(event.data)
        const { type, data } = message

        if (shouldStopRef.current) return

        switch (type) {
          case 'status':
            if (data.agents) {
              Object.entries(data.agents).forEach(([agentName, status]) => {
                const mapping = agentToTeamMap[agentName]
                if (mapping) {
                  const [teamKey, frontendName] = mapping
                  updateAgentStatus(teamKey, frontendName, status)
                }
              })
            }
            break

          case 'report':
            setReportSections((prev) => {
              const existingIndex = prev.findIndex((s) => s.key === data.section)
              const reportSection = {
                key: data.section,
                label: data.label,
                text: data.content,
              }

              if (existingIndex >= 0) {
                const newSections = [...prev]
                newSections[existingIndex] = reportSection
                return newSections
              } else {
                return [...prev, reportSection]
              }
            })
            break

          case 'complete':
            if (shouldStopRef.current) return

            console.log('Analysis complete:', data.decision)

            if (data.final_state) {
              const finalSections = []
              const sectionMap = {
                market_report: { key: 'market', label: 'Market Analysis' },
                sentiment_report: { key: 'sentiment', label: 'Social Sentiment' },
                news_report: { key: 'news', label: 'News Analysis' },
                fundamentals_report: { key: 'fundamentals', label: 'Fundamentals Review' },
                investment_plan: { key: 'investment_plan', label: 'Research Team Decision' },
                trader_investment_plan: { key: 'trader', label: 'Trader Investment Plan' },
                final_trade_decision: { key: 'final', label: 'Portfolio Management Decision' },
              }

              Object.entries(data.final_state).forEach(([key, content]) => {
                if (content && sectionMap[key]) {
                  finalSections.push({
                    key: sectionMap[key].key,
                    label: sectionMap[key].label,
                    text: content,
                  })
                }
              })

              if (finalSections.length > 0) {
                setReportSections(finalSections)

                // Extract recommendation from final_trade_decision if available
                const finalSection = finalSections.find((s) => s.key === 'final')
                if (finalSection && !data.decision) {
                  const decision = extractDecision(finalSection.text)
                  if (decision && decision !== 'REVIEW') {
                    setRecommendation(decision)
                  }
                }
              }
            }

            // Set recommendation from decision field or extract from final state
            let finalRecommendation = null
            if (data.decision) {
              const decision = extractDecision(data.decision)
              finalRecommendation = decision || data.decision
              setRecommendation(finalRecommendation)
            } else if (data.final_state?.final_trade_decision) {
              const decision = extractDecision(data.final_state.final_trade_decision)
              if (decision && decision !== 'REVIEW') {
                finalRecommendation = decision
                setRecommendation(finalRecommendation)
              }
            }

            // Update all agents to completed status
            Object.keys(agentToTeamMap).forEach((agentName) => {
              const mapping = agentToTeamMap[agentName]
              if (mapping) {
                const [teamKey, frontendName] = mapping
                updateAgentStatus(teamKey, frontendName, 'completed')
              }
            })

            // Keep connection alive - don't close it immediately
            // Only mark as not running, but keep WebSocket open for potential future updates
            shouldStopRef.current = false
            setIsRunning(false)
            
            // Keep connection open - don't close it or remove handlers
            // This allows the connection to stay alive and the recommendation to remain visible
            // The keepalive ping will continue to maintain the connection
            console.log('Analysis complete. Connection kept alive. Recommendation:', finalRecommendation || 'Not set')
            break

          case 'error':
            if (shouldStopRef.current) return
            console.error('Error:', data.message)
            setConnectionError(data.message || 'An error occurred during analysis')
            ws.close()
            wsConnectionRef.current = null
            shouldStopRef.current = false
            setIsRunning(false)
            setRecommendation('Error occurred')
            break
        }
      }

      ws.onerror = (error) => {
        clearTimeout(connectionTimeout)
        if (shouldStopRef.current) return
        console.error('WebSocket error:', error)
        const errorMsg = `Failed to connect to WebSocket. Make sure FastAPI backend is running on port 8000.`
        setConnectionError(errorMsg)
        setIsRunning(false)
        shouldStopRef.current = false
        wsConnectionRef.current = null
        setRecommendation('Connection failed')
      }

      ws.onclose = (event) => {
        clearTimeout(connectionTimeout)
        // Clear keepalive interval
        if (keepAliveIntervalRef.current) {
          clearInterval(keepAliveIntervalRef.current)
          keepAliveIntervalRef.current = null
        }
        
        if (shouldStopRef.current) return
        console.log('WebSocket closed', event.code, event.reason)
        if (event.code !== 1000 && event.code !== 1001) {
          const errorMsg = `WebSocket connection closed unexpectedly (code: ${event.code}). Make sure FastAPI backend is running.`
          setConnectionError(errorMsg)
          // Don't overwrite recommendation if analysis was already complete
          if (recommendation === 'Awaiting run' || recommendation === 'Connection timeout') {
            setRecommendation('Connection failed')
          }
        }
        setIsRunning(false)
        shouldStopRef.current = false
        wsConnectionRef.current = null
      }
    } catch (error) {
      console.error('Error starting analysis:', error)
      const errorMsg = `Failed to create WebSocket connection: ${error.message}. Make sure FastAPI backend is running on port 8000.`
      setConnectionError(errorMsg)
      setIsRunning(false)
      shouldStopRef.current = false
      wsConnectionRef.current = null
      setRecommendation('Connection failed')
    }
  }, [ticker, analysisDate, reportLength, isRunning, stopPipeline, updateAgentStatus])

  const value = {
    // State
    ticker,
    setTicker,
    analysisDate,
    setAnalysisDate,
    headerDate,
    setHeaderDate,
    reportLength,
    setReportLength,
    isRunning,
    teamState,
    reportSections,
    reportView,
    setReportView,
    recommendation,
    connectionError,
    // Actions
    runPipeline,
    stopPipeline,
    updateAgentStatus,
  }

  return <AnalysisContext.Provider value={value}>{children}</AnalysisContext.Provider>
}

export function useAnalysis() {
  const context = useContext(AnalysisContext)
  if (!context) {
    throw new Error('useAnalysis must be used within AnalysisProvider')
  }
  return context
}

