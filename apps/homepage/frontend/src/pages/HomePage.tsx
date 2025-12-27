import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { FileSpreadsheet, Presentation, BarChart3, ArrowRight, Database, GitBranch, FileText, Calendar, Settings, Bug } from 'lucide-react'
import { cn, formatDate } from '@/lib/utils'
import { useHealth } from '@/hooks/useHealth'
import { useDataSets } from '@/hooks/useDataSets'

// Check for dev mode flag from URL params or localStorage
const getDevModeEnabled = (): boolean => {
  if (typeof window === 'undefined') return false
  const urlParams = new URLSearchParams(window.location.search)
  if (urlParams.get('devmode') === 'true') {
    localStorage.setItem('devtools_enabled', 'true')
    return true
  }
  return localStorage.getItem('devtools_enabled') === 'true'
}

const tools = [
  {
    id: 'dat' as const,
    name: 'Data Aggregator',
    description: 'Parse, transform, and aggregate data from multiple sources into unified datasets.',
    icon: FileSpreadsheet,
    color: 'bg-emerald-500',
    path: '/tools/dat',
    appUrl: 'http://localhost:5173',
  },
  {
    id: 'pptx' as const,
    name: 'PowerPoint Generator',
    description: 'Generate presentation slides from data using customizable templates.',
    icon: Presentation,
    color: 'bg-orange-500',
    path: '/tools/pptx',
    appUrl: 'http://localhost:5175',
  },
  {
    id: 'sov' as const,
    name: 'SOV Analyzer',
    description: 'Perform ANOVA and variance analysis on your datasets.',
    icon: BarChart3,
    color: 'bg-purple-500',
    path: '/tools/sov',
    appUrl: 'http://localhost:5174',
  },
]

const quickActions = [
  { label: 'Browse DataSets', path: '/datasets', icon: Database },
  { label: 'View Pipelines', path: '/pipelines', icon: GitBranch },
]

const statusLabels: Record<string, string> = {
  available: 'Available',
  coming_soon: 'Coming Soon',
  maintenance: 'Maintenance',
  error: 'Error',
}

export function HomePage() {
  const { data: health } = useHealth()
  // Datasets endpoint not yet implemented, so disable this query
  const { data: recentDatasets, isLoading: datasetsLoading } = useDataSets({ limit: 5 }, false)
  const [devToolsEnabled, setDevToolsEnabled] = useState(getDevModeEnabled)
  const [showDebugPanel, setShowDebugPanel] = useState(false)

  // Update localStorage when devToolsEnabled changes
  useEffect(() => {
    if (devToolsEnabled) {
      localStorage.setItem('devtools_enabled', 'true')
    } else {
      localStorage.removeItem('devtools_enabled')
    }
  }, [devToolsEnabled])

  const getToolStatus = (toolId: 'dat' | 'sov' | 'pptx') => {
    return health?.tools?.[toolId] || 'coming_soon'
  }

  return (
    <div className="space-y-8">
      {/* Debug Panel - Always visible, toggles DevTools */}
      <div className="fixed bottom-4 right-4 z-50">
        <button
          onClick={() => setShowDebugPanel(!showDebugPanel)}
          className="p-2 bg-slate-800 text-white rounded-full shadow-lg hover:bg-slate-700 transition-colors"
          title="Toggle Debug Panel"
          aria-label="Toggle Debug Panel"
        >
          <Bug className="w-5 h-5" />
        </button>
        {showDebugPanel && (
          <div className="absolute bottom-12 right-0 w-64 bg-white rounded-lg shadow-xl border border-slate-200 p-4">
            <h3 className="font-semibold text-slate-900 mb-3 flex items-center gap-2">
              <Settings className="w-4 h-4" />
              Power User Panel
            </h3>
            <div className="space-y-3">
              <label className="flex items-center justify-between">
                <span className="text-sm text-slate-700">Enable DevTools</span>
                <button
                  onClick={() => setDevToolsEnabled(!devToolsEnabled)}
                  className={cn(
                    'relative w-10 h-5 rounded-full transition-colors',
                    devToolsEnabled ? 'bg-cyan-500' : 'bg-slate-300'
                  )}
                >
                  <span
                    className={cn(
                      'absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-transform shadow',
                      devToolsEnabled && 'translate-x-5'
                    )}
                  />
                </button>
              </label>
              {devToolsEnabled && (
                <Link
                  to="/devtools"
                  className="block w-full text-center px-3 py-2 bg-cyan-500 text-white rounded-md text-sm font-medium hover:bg-cyan-600 transition-colors"
                >
                  Open DevTools
                </Link>
              )}
              <p className="text-xs text-slate-500">
                Tip: Add ?devmode=true to URL to enable
              </p>
            </div>
          </div>
        )}
      </div>

      <div className="text-center max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold text-slate-900">Engineering Tools Platform</h1>
        <p className="mt-3 text-lg text-slate-600">
          A unified platform for data processing, analysis, and presentation generation.
        </p>
      </div>

      <div className={cn('grid gap-6', devToolsEnabled ? 'md:grid-cols-4' : 'md:grid-cols-3')}>
        {tools.map((tool) => {
          const status = getToolStatus(tool.id)
          const isDisabled = status !== 'available'
          return (
            <Link
              key={tool.id}
              to={tool.path}
              className={cn(
                'group relative bg-white rounded-xl border border-slate-200 p-6 shadow-sm transition-all hover:shadow-md hover:border-slate-300',
                isDisabled && 'opacity-75'
              )}
            >
              <div className={cn('w-12 h-12 rounded-lg flex items-center justify-center', tool.color)}>
                <tool.icon className="w-6 h-6 text-white" />
              </div>
              <h3 className="mt-4 text-lg font-semibold text-slate-900 group-hover:text-primary-600">
                {tool.name}
              </h3>
              <p className="mt-2 text-sm text-slate-600">{tool.description}</p>
              {status !== 'available' && (
                <span className="absolute top-4 right-4 text-xs bg-slate-100 text-slate-600 px-2 py-1 rounded-full">
                  {statusLabels[status] || status}
                </span>
              )}
              <div className="mt-4 flex items-center text-sm font-medium text-primary-600 group-hover:text-primary-700">
                Open Tool
                <ArrowRight className="ml-1 w-4 h-4 transition-transform group-hover:translate-x-1" />
              </div>
            </Link>
          )
        })}
        
        {/* DevTools Card - Only visible when enabled */}
        {devToolsEnabled && (
          <Link
            to="/devtools"
            className="group relative bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl border border-slate-700 p-6 shadow-sm transition-all hover:shadow-md hover:border-slate-600"
          >
            <div className="w-12 h-12 rounded-lg flex items-center justify-center bg-cyan-500">
              <Settings className="w-6 h-6 text-white" />
            </div>
            <h3 className="mt-4 text-lg font-semibold text-white group-hover:text-cyan-400">
              DevTools
            </h3>
            <p className="mt-2 text-sm text-slate-400">
              ADR editor, config management, and developer utilities.
            </p>
            <span className="absolute top-4 right-4 text-xs bg-cyan-500/20 text-cyan-400 px-2 py-1 rounded-full">
              Developer
            </span>
            <div className="mt-4 flex items-center text-sm font-medium text-cyan-400 group-hover:text-cyan-300">
              Open DevTools
              <ArrowRight className="ml-1 w-4 h-4 transition-transform group-hover:translate-x-1" />
            </div>
          </Link>
        )}
      </div>

      {/* Recent DataSets Section */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-slate-900">Recent DataSets</h2>
          <Link to="/datasets" className="text-sm text-primary-600 hover:text-primary-700 font-medium">
            View All →
          </Link>
        </div>
        {datasetsLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600" />
          </div>
        ) : recentDatasets && recentDatasets.length > 0 ? (
          <div className="space-y-3">
            {recentDatasets.map((dataset) => (
              <div
                key={dataset.dataset_id}
                className="flex items-center justify-between p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <Database className="w-4 h-4 text-slate-400" />
                  <div>
                    <div className="font-medium text-slate-900">{dataset.name}</div>
                    <div className="flex items-center gap-2 text-xs text-slate-500">
                      <span className="uppercase">{dataset.created_by_tool}</span>
                      <span>•</span>
                      <span className="flex items-center gap-1">
                        <FileText className="w-3 h-3" />
                        {dataset.row_count.toLocaleString()} rows
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-1 text-xs text-slate-500">
                  <Calendar className="w-3 h-3" />
                  {formatDate(dataset.created_at)}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-slate-500">
            <Database className="w-8 h-8 mx-auto mb-2 text-slate-300" />
            <p className="text-sm">No datasets yet. Export data from any tool to create one.</p>
          </div>
        )}
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h2 className="text-lg font-semibold text-slate-900">Quick Actions</h2>
        <div className="mt-4 flex gap-4">
          {quickActions.map((action) => (
            <Link
              key={action.path}
              to={action.path}
              className="flex items-center gap-2 px-4 py-2 bg-slate-50 hover:bg-slate-100 rounded-lg text-sm font-medium text-slate-700 transition-colors"
            >
              <action.icon className="w-4 h-4" />
              {action.label}
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
