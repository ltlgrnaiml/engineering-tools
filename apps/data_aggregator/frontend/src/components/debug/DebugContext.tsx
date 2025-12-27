import React, { createContext, useContext, useState, useCallback, useRef } from 'react'

export type LogLevel = 'info' | 'warn' | 'error' | 'success' | 'debug'

export interface DebugLogEntry {
  id: string
  timestamp: Date
  level: LogLevel
  category: 'api' | 'state' | 'render' | 'user' | 'system'
  message: string
  details?: unknown
  duration?: number
  source?: string
}

export interface APICallEntry {
  id: string
  timestamp: Date
  method: string
  url: string
  requestBody?: unknown
  responseStatus?: number
  responseBody?: unknown
  duration?: number
  error?: string
  pending: boolean
}

export interface StateTransition {
  id: string
  timestamp: Date
  from: string
  to: string
  trigger: string
  payload?: unknown
}

interface DebugContextValue {
  logs: DebugLogEntry[]
  apiCalls: APICallEntry[]
  stateTransitions: StateTransition[]
  isEnabled: boolean
  isPanelOpen: boolean
  
  log: (level: LogLevel, category: DebugLogEntry['category'], message: string, details?: unknown, source?: string) => void
  logAPI: (entry: Omit<APICallEntry, 'id' | 'timestamp'>) => string
  updateAPI: (id: string, updates: Partial<APICallEntry>) => void
  logStateTransition: (from: string, to: string, trigger: string, payload?: unknown) => void
  
  clearLogs: () => void
  togglePanel: () => void
  setEnabled: (enabled: boolean) => void
  exportLogs: () => string
}

const DebugContext = createContext<DebugContextValue | null>(null)

let logIdCounter = 0
const generateId = () => `log-${Date.now()}-${++logIdCounter}`

export function DebugProvider({ children }: { children: React.ReactNode }) {
  const [logs, setLogs] = useState<DebugLogEntry[]>([])
  const [apiCalls, setApiCalls] = useState<APICallEntry[]>([])
  const [stateTransitions, setStateTransitions] = useState<StateTransition[]>([])
  const [isEnabled, setEnabled] = useState(true)
  const [isPanelOpen, setIsPanelOpen] = useState(false)
  
  const maxLogs = useRef(500)

  const log = useCallback((
    level: LogLevel,
    category: DebugLogEntry['category'],
    message: string,
    details?: unknown,
    source?: string
  ) => {
    if (!isEnabled) return
    
    const entry: DebugLogEntry = {
      id: generateId(),
      timestamp: new Date(),
      level,
      category,
      message,
      details,
      source,
    }
    
    setLogs((prev: DebugLogEntry[]) => {
      const next = [entry, ...prev]
      return next.slice(0, maxLogs.current)
    })
    
    // Also log to console for developer tools
    const consoleMethod = level === 'error' ? 'error' : level === 'warn' ? 'warn' : 'log'
    console[consoleMethod](`[${category.toUpperCase()}] ${message}`, details || '')
  }, [isEnabled])

  const logAPI = useCallback((entry: Omit<APICallEntry, 'id' | 'timestamp'>): string => {
    const id = generateId()
    const fullEntry: APICallEntry = {
      ...entry,
      id,
      timestamp: new Date(),
    }
    
    setApiCalls((prev: APICallEntry[]) => {
      const next = [fullEntry, ...prev]
      return next.slice(0, maxLogs.current)
    })
    
    log('info', 'api', `${entry.method} ${entry.url}`, entry.requestBody, 'fetch')
    
    return id
  }, [log])

  const updateAPI = useCallback((id: string, updates: Partial<APICallEntry>) => {
    setApiCalls((prev: APICallEntry[]) => prev.map((call: APICallEntry) => 
      call.id === id ? { ...call, ...updates } : call
    ))
    
    if (updates.error) {
      log('error', 'api', `API Error: ${updates.error}`, { id, ...updates }, 'fetch')
    } else if (updates.responseStatus) {
      const level = updates.responseStatus >= 400 ? 'error' : 'success'
      log(level, 'api', `Response ${updates.responseStatus}`, updates.responseBody, 'fetch')
    }
  }, [log])

  const logStateTransition = useCallback((from: string, to: string, trigger: string, payload?: unknown) => {
    if (!isEnabled) return
    
    const entry: StateTransition = {
      id: generateId(),
      timestamp: new Date(),
      from,
      to,
      trigger,
      payload,
    }
    
    setStateTransitions((prev: StateTransition[]) => {
      const next = [entry, ...prev]
      return next.slice(0, maxLogs.current)
    })
    
    log('info', 'state', `${from} → ${to} (${trigger})`, payload, 'state-machine')
  }, [isEnabled, log])

  const clearLogs = useCallback(() => {
    setLogs([])
    setApiCalls([])
    setStateTransitions([])
  }, [])

  const togglePanel = useCallback(() => {
    setIsPanelOpen((prev: boolean) => !prev)
  }, [])

  const exportLogs = useCallback(() => {
    const exportData = {
      exportedAt: new Date().toISOString(),
      logs,
      apiCalls,
      stateTransitions,
    }
    return JSON.stringify(exportData, null, 2)
  }, [logs, apiCalls, stateTransitions])

  return (
    <DebugContext.Provider value={{
      logs,
      apiCalls,
      stateTransitions,
      isEnabled,
      isPanelOpen,
      log,
      logAPI,
      updateAPI,
      logStateTransition,
      clearLogs,
      togglePanel,
      setEnabled,
      exportLogs,
    }}>
      {children}
    </DebugContext.Provider>
  )
}

export function useDebug() {
  const context = useContext(DebugContext)
  if (!context) {
    throw new Error('useDebug must be used within a DebugProvider')
  }
  return context
}

// Hook to check if debug context is available (for optional usage)
export function useDebugOptional() {
  return useContext(DebugContext)
}
