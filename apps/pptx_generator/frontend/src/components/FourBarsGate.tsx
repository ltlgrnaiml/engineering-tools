import { useState } from 'react'
import { CheckCircle, AlertCircle, XCircle, ChevronDown, ChevronRight } from 'lucide-react'
import type { FourBarsStatus, BarStatus } from '../types'

interface FourBarsGateProps {
  status: FourBarsStatus
  onBuildPlan: () => void
  building: boolean
}

export function FourBarsGate({ status, onBuildPlan, building }: FourBarsGateProps) {
  const [expandedBar, setExpandedBar] = useState<string | null>(null)

  const allGreen = (
    status.required_context.status === 'green' &&
    status.required_metrics.status === 'green' &&
    status.required_data_levels.status === 'green' &&
    status.required_renderers.status === 'green'
  )

  console.log('[DEBUG FourBarsGate] Rendered with allGreen:', allGreen, 'building:', building)

  const bars = [
    { id: 'context', label: 'Required Context', data: status.required_context },
    { id: 'metrics', label: 'Required Metrics', data: status.required_metrics },
    { id: 'data_levels', label: 'Required Data Levels', data: status.required_data_levels },
    { id: 'renderers', label: 'Required Renderers', data: status.required_renderers },
  ]

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Four Green Bars Validation
        </h2>
        <p className="text-gray-600">
          All four bars must be green to proceed with plan building
        </p>
      </div>

      <div className="space-y-3">
        {bars.map((bar) => (
          <BarDisplay
            key={bar.id}
            id={bar.id}
            label={bar.label}
            status={bar.data}
            expanded={expandedBar === bar.id}
            onToggle={() => setExpandedBar(expandedBar === bar.id ? null : bar.id)}
          />
        ))}
      </div>

      <div className="text-center pt-4">
        <button
          type="button"
          onClick={(e) => {
            console.log('[DEBUG FourBarsGate] Build Plan button clicked')
            e.preventDefault()
            e.stopPropagation()
            console.log('[DEBUG FourBarsGate] Calling onBuildPlan')
            onBuildPlan()
            console.log('[DEBUG FourBarsGate] onBuildPlan called')
          }}
          disabled={!allGreen || building}
          className={
            `px-8 py-3 rounded-lg font-semibold transition-colors ${
              allGreen && !building
                ? 'bg-green-600 text-white hover:bg-green-700'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }`
          }
        >
          {building ? 'Building Plan...' : 'Build Plan'}
        </button>
        {!allGreen && (
          <p className="mt-2 text-sm text-red-600">
            Please resolve all validation issues before building plan
          </p>
        )}
      </div>
    </div>
  )
}

interface BarDisplayProps {
  id: string
  label: string
  status: BarStatus
  expanded: boolean
  onToggle: () => void
}

function BarDisplay({ label, status, expanded, onToggle }: BarDisplayProps) {
  const getStatusIcon = () => {
    switch (status.status) {
      case 'green':
        return <CheckCircle className="h-6 w-6 text-green-600" />
      case 'yellow':
        return <AlertCircle className="h-6 w-6 text-yellow-600" />
      case 'red':
        return <XCircle className="h-6 w-6 text-red-600" />
    }
  }

  const getStatusColor = () => {
    switch (status.status) {
      case 'green':
        return 'bg-green-50 border-green-200'
      case 'yellow':
        return 'bg-yellow-50 border-yellow-200'
      case 'red':
        return 'bg-red-50 border-red-200'
    }
  }

  const hasIssues = status.missing_items.length > 0 || status.warnings.length > 0

  return (
    <div className={`border-2 rounded-lg ${getStatusColor()}`}>
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 flex items-center justify-between hover:opacity-80 transition-opacity"
      >
        <div className="flex items-center gap-3">
          {getStatusIcon()}
          <span className="font-semibold text-gray-900">{label}</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-gray-700">
            {status.coverage_percentage.toFixed(0)}% Complete
          </span>
          {hasIssues && (
            expanded ? <ChevronDown className="h-5 w-5" /> : <ChevronRight className="h-5 w-5" />
          )}
        </div>
      </button>

      {expanded && hasIssues && (
        <div className="px-4 pb-3 space-y-2">
          {status.missing_items.length > 0 && (
            <div>
              <p className="text-sm font-medium text-gray-700 mb-1">Missing Items:</p>
              <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                {status.missing_items.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>
          )}
          {status.warnings.length > 0 && (
            <div>
              <p className="text-sm font-medium text-gray-700 mb-1">Warnings:</p>
              <div className="space-y-2">
                {status.warnings.map((warning, idx) => (
                  <div key={idx} className="text-sm">
                    <p className="text-gray-800">{warning.message}</p>
                    {warning.suggested_fix && (
                      <p className="text-blue-600 mt-1">→ {warning.suggested_fix}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
