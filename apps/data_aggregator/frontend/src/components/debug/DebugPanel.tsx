import { useState } from 'react'
import { 
  Bug, X, Trash2, Download, ChevronDown, ChevronRight, 
  AlertCircle, CheckCircle, Info, AlertTriangle,
  Network, Layers, RefreshCw, Copy, Eye, EyeOff
} from 'lucide-react'
import { useDebug, type DebugLogEntry, type APICallEntry, type StateTransition } from './DebugContext'

type Tab = 'logs' | 'api' | 'state'

function formatTime(date: Date): string {
  const ms = date.getMilliseconds().toString().padStart(3, '0')
  return date.toLocaleTimeString('en-US', { 
    hour12: false, 
    hour: '2-digit', 
    minute: '2-digit', 
    second: '2-digit',
  }) + '.' + ms
}

function LogLevelIcon({ level }: { level: DebugLogEntry['level'] }) {
  switch (level) {
    case 'error': return <AlertCircle className="w-4 h-4 text-red-500" />
    case 'warn': return <AlertTriangle className="w-4 h-4 text-yellow-500" />
    case 'success': return <CheckCircle className="w-4 h-4 text-green-500" />
    case 'debug': return <Bug className="w-4 h-4 text-purple-500" />
    default: return <Info className="w-4 h-4 text-blue-500" />
  }
}

function JSONViewer({ data, collapsed = true }: { data: unknown; collapsed?: boolean }) {
  const [isCollapsed, setIsCollapsed] = useState(collapsed)
  
  if (data === undefined || data === null) {
    return <span className="text-slate-400 italic">null</span>
  }
  
  let jsonString: string
  try {
    jsonString = typeof data === 'string' ? data : JSON.stringify(data, null, 2)
  } catch {
    jsonString = String(data)
  }
  
  if (jsonString.length < 100 && !jsonString.includes('\n')) {
    return <code className="text-xs bg-slate-800 px-1 rounded text-emerald-400">{jsonString}</code>
  }
  
  return (
    <div className="mt-1">
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-300"
      >
        {isCollapsed ? <ChevronRight className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        {isCollapsed ? 'Show details' : 'Hide details'}
      </button>
      {!isCollapsed && (
        <pre className="mt-1 p-2 bg-slate-800 rounded text-xs overflow-x-auto max-h-48 overflow-y-auto text-slate-300">
          {jsonString}
        </pre>
      )}
    </div>
  )
}

function LogEntry({ entry }: { entry: DebugLogEntry }) {
  return (
    <div className={`px-3 py-2 border-b border-slate-700 hover:bg-slate-800/50 ${
      entry.level === 'error' ? 'bg-red-950/20' : ''
    }`}>
      <div className="flex items-start gap-2">
        <LogLevelIcon level={entry.level} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-500 font-mono">{formatTime(entry.timestamp)}</span>
            <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${
              entry.category === 'api' ? 'bg-blue-900 text-blue-300' :
              entry.category === 'state' ? 'bg-purple-900 text-purple-300' :
              entry.category === 'user' ? 'bg-green-900 text-green-300' :
              'bg-slate-700 text-slate-300'
            }`}>
              {entry.category}
            </span>
            {entry.source && (
              <span className="text-slate-500 text-xs">{entry.source}</span>
            )}
          </div>
          <p className="text-sm text-slate-200 mt-1">{entry.message}</p>
          {entry.details !== undefined && <JSONViewer data={entry.details} />}
        </div>
      </div>
    </div>
  )
}

function APICallRow({ call }: { call: APICallEntry }) {
  const [expanded, setExpanded] = useState(false)
  
  const statusColor = call.pending ? 'text-yellow-400' :
    call.responseStatus && call.responseStatus >= 400 ? 'text-red-400' :
    call.responseStatus && call.responseStatus < 300 ? 'text-green-400' :
    'text-slate-400'
  
  const methodColor = {
    GET: 'bg-blue-900 text-blue-300',
    POST: 'bg-green-900 text-green-300',
    PUT: 'bg-yellow-900 text-yellow-300',
    DELETE: 'bg-red-900 text-red-300',
    PATCH: 'bg-purple-900 text-purple-300',
  }[call.method] || 'bg-slate-700 text-slate-300'
  
  return (
    <div className={`border-b border-slate-700 ${call.error ? 'bg-red-950/20' : ''}`}>
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-3 py-2 flex items-center gap-2 hover:bg-slate-800/50 text-left"
      >
        {expanded ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
        
        <span className="text-slate-500 font-mono text-xs w-20">{formatTime(call.timestamp)}</span>
        
        <span className={`px-1.5 py-0.5 rounded text-xs font-bold ${methodColor}`}>
          {call.method}
        </span>
        
        <span className="flex-1 text-sm text-slate-300 truncate font-mono">{call.url}</span>
        
        {call.pending ? (
          <RefreshCw className="w-4 h-4 text-yellow-400 animate-spin" />
        ) : (
          <span className={`text-sm font-mono ${statusColor}`}>
            {call.responseStatus || 'ERR'}
          </span>
        )}
        
        {call.duration && (
          <span className="text-xs text-slate-500 w-16 text-right">{call.duration}ms</span>
        )}
      </button>
      
      {expanded && (
        <div className="px-3 pb-3 space-y-2">
          {call.requestBody && (
            <div>
              <div className="text-xs font-medium text-slate-400 mb-1">Request Body:</div>
              <pre className="p-2 bg-slate-800 rounded text-xs overflow-x-auto max-h-32 overflow-y-auto text-slate-300">
                {JSON.stringify(call.requestBody, null, 2)}
              </pre>
            </div>
          )}
          {call.responseBody && (
            <div>
              <div className="text-xs font-medium text-slate-400 mb-1">Response Body:</div>
              <pre className="p-2 bg-slate-800 rounded text-xs overflow-x-auto max-h-32 overflow-y-auto text-slate-300">
                {typeof call.responseBody === 'string' ? call.responseBody : JSON.stringify(call.responseBody, null, 2)}
              </pre>
            </div>
          )}
          {call.error && (
            <div>
              <div className="text-xs font-medium text-red-400 mb-1">Error:</div>
              <pre className="p-2 bg-red-900/30 rounded text-xs text-red-300">{call.error}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function StateTransitionRow({ transition }: { transition: StateTransition }) {
  return (
    <div className="px-3 py-2 border-b border-slate-700 hover:bg-slate-800/50">
      <div className="flex items-center gap-2">
        <span className="text-slate-500 font-mono text-xs">{formatTime(transition.timestamp)}</span>
        <span className="px-2 py-0.5 bg-slate-700 rounded text-xs text-slate-300">{transition.from}</span>
        <span className="text-slate-500">→</span>
        <span className="px-2 py-0.5 bg-emerald-900 rounded text-xs text-emerald-300">{transition.to}</span>
        <span className="text-xs text-slate-400 italic">({transition.trigger})</span>
      </div>
      {transition.payload && <JSONViewer data={transition.payload} />}
    </div>
  )
}

export function DebugPanel() {
  const { 
    logs, apiCalls, stateTransitions, 
    isPanelOpen, isEnabled,
    togglePanel, clearLogs, setEnabled, exportLogs 
  } = useDebug()
  
  const [activeTab, setActiveTab] = useState<Tab>('api')
  const [filter, setFilter] = useState('')
  
  const handleExport = () => {
    const data = exportLogs()
    const blob = new Blob([data], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `debug-logs-${new Date().toISOString().split('T')[0]}.json`
    a.click()
    URL.revokeObjectURL(url)
  }
  
  const handleCopy = () => {
    navigator.clipboard.writeText(exportLogs())
  }
  
  const filteredLogs = logs.filter(log => 
    !filter || log.message.toLowerCase().includes(filter.toLowerCase())
  )
  
  const filteredApiCalls = apiCalls.filter(call =>
    !filter || call.url.toLowerCase().includes(filter.toLowerCase())
  )
  
  // Floating debug button when panel is closed
  if (!isPanelOpen) {
    return (
      <button
        onClick={togglePanel}
        className="fixed bottom-4 right-4 z-50 p-3 bg-slate-800 hover:bg-slate-700 text-white rounded-full shadow-lg border border-slate-600 flex items-center gap-2"
        title="Open Debug Panel"
      >
        <Bug className="w-5 h-5" />
        {(apiCalls.some(c => c.error) || logs.some(l => l.level === 'error')) && (
          <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full animate-pulse" />
        )}
      </button>
    )
  }
  
  return (
    <div className="fixed bottom-0 right-0 z-50 w-full md:w-[600px] lg:w-[800px] h-[400px] bg-slate-900 border-t border-l border-slate-700 shadow-2xl flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-slate-700 bg-slate-800">
        <div className="flex items-center gap-3">
          <Bug className="w-5 h-5 text-emerald-400" />
          <span className="font-semibold text-white">Debug Panel</span>
          <span className="text-xs text-slate-400">
            {apiCalls.length} API calls • {logs.length} logs
          </span>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => setEnabled(!isEnabled)}
            className={`p-1.5 rounded ${isEnabled ? 'text-emerald-400 hover:bg-slate-700' : 'text-slate-500 hover:bg-slate-700'}`}
            title={isEnabled ? 'Pause logging' : 'Resume logging'}
          >
            {isEnabled ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
          </button>
          <button
            onClick={handleCopy}
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded"
            title="Copy logs to clipboard"
          >
            <Copy className="w-4 h-4" />
          </button>
          <button
            onClick={handleExport}
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded"
            title="Export logs"
          >
            <Download className="w-4 h-4" />
          </button>
          <button
            onClick={clearLogs}
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded"
            title="Clear logs"
          >
            <Trash2 className="w-4 h-4" />
          </button>
          <button
            onClick={togglePanel}
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded"
            title="Close panel"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
      
      {/* Tabs */}
      <div className="flex items-center border-b border-slate-700 bg-slate-800/50">
        <button
          onClick={() => setActiveTab('api')}
          className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'api' 
              ? 'border-emerald-400 text-emerald-400' 
              : 'border-transparent text-slate-400 hover:text-white'
          }`}
        >
          <Network className="w-4 h-4" />
          API Calls
          {apiCalls.some(c => c.error) && (
            <span className="w-2 h-2 bg-red-500 rounded-full" />
          )}
        </button>
        <button
          onClick={() => setActiveTab('logs')}
          className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'logs' 
              ? 'border-emerald-400 text-emerald-400' 
              : 'border-transparent text-slate-400 hover:text-white'
          }`}
        >
          <Info className="w-4 h-4" />
          All Logs
          {logs.some(l => l.level === 'error') && (
            <span className="w-2 h-2 bg-red-500 rounded-full" />
          )}
        </button>
        <button
          onClick={() => setActiveTab('state')}
          className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'state' 
              ? 'border-emerald-400 text-emerald-400' 
              : 'border-transparent text-slate-400 hover:text-white'
          }`}
        >
          <Layers className="w-4 h-4" />
          State
        </button>
        
        {/* Search */}
        <div className="flex-1 px-4">
          <input
            type="text"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Filter..."
            className="w-full px-3 py-1 text-sm bg-slate-800 border border-slate-600 rounded text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
          />
        </div>
      </div>
      
      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'api' && (
          <div>
            {filteredApiCalls.length === 0 ? (
              <div className="flex items-center justify-center h-full text-slate-500">
                <div className="text-center">
                  <Network className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>No API calls recorded</p>
                </div>
              </div>
            ) : (
              filteredApiCalls.map(call => <APICallRow key={call.id} call={call} />)
            )}
          </div>
        )}
        
        {activeTab === 'logs' && (
          <div>
            {filteredLogs.length === 0 ? (
              <div className="flex items-center justify-center h-full text-slate-500">
                <div className="text-center">
                  <Info className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>No logs recorded</p>
                </div>
              </div>
            ) : (
              filteredLogs.map(entry => <LogEntry key={entry.id} entry={entry} />)
            )}
          </div>
        )}
        
        {activeTab === 'state' && (
          <div>
            {stateTransitions.length === 0 ? (
              <div className="flex items-center justify-center h-full text-slate-500">
                <div className="text-center">
                  <Layers className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>No state transitions recorded</p>
                </div>
              </div>
            ) : (
              stateTransitions.map(t => <StateTransitionRow key={t.id} transition={t} />)
            )}
          </div>
        )}
      </div>
    </div>
  )
}
