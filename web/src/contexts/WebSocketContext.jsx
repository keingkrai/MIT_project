import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react'

const WebSocketContext = createContext(null)

export function WebSocketProvider({ children }) {
  const [debugState, setDebugState] = useState({
    wsConnected: false,
    wsUrl: '',
    messageCount: 0,
    errorCount: 0,
    lastUpdate: null,
    lastType: null,
    logEntries: [],
    maxLogEntries: 50,
  })
  const wsRef = useRef(null)
  const reconnectTimeoutRef = useRef(null)
  const reconnectAttempts = useRef(0)
  const maxReconnectAttempts = 5

  const addDebugLog = useCallback((type, content, isError = false) => {
    const time = new Date().toLocaleTimeString()
    setDebugState((prev) => {
      const newEntries = [
        ...prev.logEntries,
        {
          time,
          type,
          content: String(content),
        },
      ]
      // Keep only last N entries
      const trimmedEntries =
        newEntries.length > prev.maxLogEntries
          ? newEntries.slice(-prev.maxLogEntries)
          : newEntries

      return {
        ...prev,
        logEntries: trimmedEntries,
        messageCount: prev.messageCount + 1,
        lastUpdate: new Date().toISOString(),
        lastType: type,
        errorCount: isError ? prev.errorCount + 1 : prev.errorCount,
      }
    })
  }, [])

  const getWebSocketUrl = useCallback(() => {
    const isDevelopment = import.meta.env.DEV
    const isFileProtocol = window.location.protocol === 'file:'

    if (isFileProtocol || window.location.hostname === '') {
      return 'ws://localhost:8000/ws'
    } else if (isDevelopment) {
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      return `${wsProtocol}//${window.location.host}/ws`
    } else {
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsHost = window.location.hostname
      const wsPort = window.location.port || (window.location.protocol === 'https:' ? '443' : '8000')
      return `${wsProtocol}//${wsHost}:${wsPort}/ws`
    }
  }, [])

  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return // Already connected
    }

    const wsUrl = getWebSocketUrl()
    addDebugLog('system', `Attempting to connect to ${wsUrl}`)

    try {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        reconnectAttempts.current = 0
        setDebugState((prev) => ({
          ...prev,
          wsConnected: true,
          wsUrl: wsUrl,
        }))
        addDebugLog('system', 'WebSocket connected successfully', false)
      }

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          const { type, data } = message
          addDebugLog(type, JSON.stringify(data).substring(0, 200), type === 'error')
        } catch (error) {
          addDebugLog('error', `Failed to parse message: ${error.message}`, true)
        }
      }

      ws.onerror = (error) => {
        addDebugLog('error', `WebSocket error: ${error.message || 'Connection error'}`, true)
        setDebugState((prev) => ({
          ...prev,
          wsConnected: false,
        }))
      }

      ws.onclose = (event) => {
        setDebugState((prev) => ({
          ...prev,
          wsConnected: false,
        }))

        if (event.code !== 1000 && event.code !== 1001) {
          // Not a normal closure - attempt to reconnect
          if (reconnectAttempts.current < maxReconnectAttempts) {
            reconnectAttempts.current++
            const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 10000)
            addDebugLog(
              'system',
              `Connection closed. Reconnecting in ${delay / 1000}s... (attempt ${reconnectAttempts.current}/${maxReconnectAttempts})`,
              false
            )
            reconnectTimeoutRef.current = setTimeout(() => {
              connectWebSocket()
            }, delay)
          } else {
            addDebugLog('error', 'Max reconnection attempts reached', true)
          }
        } else {
          addDebugLog('system', 'WebSocket closed normally', false)
        }
      }
    } catch (error) {
      addDebugLog('error', `Failed to create WebSocket: ${error.message}`, true)
    }
  }, [getWebSocketUrl, addDebugLog])

  const disconnectWebSocket = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setDebugState((prev) => ({
      ...prev,
      wsConnected: false,
    }))
  }, [])

  const checkBackendHealth = useCallback(async () => {
    try {
      // Always use the backend URL directly (not through Vite proxy)
      const isDevelopment = import.meta.env.DEV
      const isFileProtocol = window.location.protocol === 'file:'
      
      let baseUrl
      if (isFileProtocol || window.location.hostname === '') {
        baseUrl = 'http://localhost:8000'
      } else if (isDevelopment) {
        // In development, Vite runs on different port, use backend directly
        baseUrl = 'http://localhost:8000'
      } else {
        // Production - same hostname
        baseUrl = `${window.location.protocol}//${window.location.hostname}:8000`
      }
      
      const response = await fetch(`${baseUrl}/api/health`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      })
      
      if (response.ok) {
        const contentType = response.headers.get('content-type')
        if (contentType && contentType.includes('application/json')) {
          const data = await response.json()
          addDebugLog('system', `Backend health check: ${data.status}`, false)
          // If backend is healthy and not connected, connect
          if (!debugState.wsConnected && wsRef.current?.readyState !== WebSocket.OPEN) {
            connectWebSocket()
          }
          return true
        } else {
          // Got HTML instead of JSON - backend might not be running or wrong endpoint
          addDebugLog('error', `Backend returned HTML instead of JSON. Check if FastAPI is running on ${baseUrl}`, true)
          return false
        }
      } else {
        addDebugLog('error', `Backend health check returned status: ${response.status}`, true)
        return false
      }
    } catch (error) {
      // Network error or CORS issue
      addDebugLog('error', `Backend health check failed: ${error.message}. Make sure FastAPI is running on port 8000.`, true)
      return false
    }
  }, [connectWebSocket, debugState.wsConnected, addDebugLog])

  // Connect on mount and check backend health
  useEffect(() => {
    // First check if backend is available, then connect
    const initializeConnection = async () => {
      const isHealthy = await checkBackendHealth()
      if (isHealthy) {
        connectWebSocket()
      } else {
        // Retry connection after 2 seconds if backend not ready
        setTimeout(() => {
          checkBackendHealth().then((healthy) => {
            if (healthy) connectWebSocket()
          })
        }, 2000)
      }
    }

    initializeConnection()

    // Set up periodic health checks if not connected
    const healthCheckInterval = setInterval(() => {
      setDebugState((prev) => {
        if (!prev.wsConnected) {
          checkBackendHealth().then((healthy) => {
            if (healthy) connectWebSocket()
          })
        }
        return prev
      })
    }, 5000) // Check every 5 seconds if not connected

    return () => {
      clearInterval(healthCheckInterval)
      disconnectWebSocket()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []) // Only run on mount

  const clearDebugLog = useCallback(() => {
    setDebugState((prev) => ({
      ...prev,
      logEntries: [],
      messageCount: 0,
      errorCount: 0,
    }))
  }, [])

  const value = {
    debugState,
    wsConnection: wsRef.current,
    connectWebSocket,
    disconnectWebSocket,
    addDebugLog,
    checkBackendHealth,
    clearDebugLog,
  }

  return <WebSocketContext.Provider value={value}>{children}</WebSocketContext.Provider>
}

export function useWebSocket() {
  const context = useContext(WebSocketContext)
  if (!context) {
    throw new Error('useWebSocket must be used within WebSocketProvider')
  }
  return context
}

