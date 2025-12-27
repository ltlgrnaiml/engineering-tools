import { useState, useRef, useEffect } from 'react'
import { ChevronDown, Sparkles, Wand2, Settings } from 'lucide-react'

interface MappingActionDropdownProps {
  onApplyContextDefaults: () => Promise<void>
  onApplyMetricDefaults: () => Promise<void>
  onApplyAllDefaults: () => Promise<void>
  onAutoSuggestContexts?: () => Promise<void>
  onAutoSuggestMetrics?: () => Promise<void>
  disabled?: boolean
  loading?: boolean
}

export function MappingActionDropdown({
  onApplyContextDefaults,
  onApplyMetricDefaults,
  onApplyAllDefaults,
  onAutoSuggestContexts,
  onAutoSuggestMetrics,
  disabled = false,
  loading = false,
}: MappingActionDropdownProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [activeAction, setActiveAction] = useState<string | null>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleAction = async (actionName: string, action: () => Promise<void>) => {
    setActiveAction(actionName)
    try {
      await action()
    } finally {
      setActiveAction(null)
      setIsOpen(false)
    }
  }

  const isActionLoading = (actionName: string) => activeAction === actionName

  return (
    <div className="relative inline-block" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled || loading}
        className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center gap-2 transition-colors"
      >
        <Sparkles className="h-4 w-4" />
        <span>Apply Defaults</span>
        <ChevronDown className={`h-4 w-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50">
          <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
            Apply Defaults
          </div>

          <button
            onClick={() => handleAction('contexts', onApplyContextDefaults)}
            disabled={isActionLoading('contexts')}
            className="w-full px-4 py-2 text-left hover:bg-purple-50 flex items-center gap-3 transition-colors"
          >
            <Settings className="h-4 w-4 text-purple-600" />
            <div>
              <div className="font-medium text-gray-900">Context Defaults Only</div>
              <div className="text-xs text-gray-500">Apply default context mappings</div>
            </div>
            {isActionLoading('contexts') && (
              <div className="ml-auto animate-spin h-4 w-4 border-2 border-purple-600 border-t-transparent rounded-full" />
            )}
          </button>

          <button
            onClick={() => handleAction('metrics', onApplyMetricDefaults)}
            disabled={isActionLoading('metrics')}
            className="w-full px-4 py-2 text-left hover:bg-purple-50 flex items-center gap-3 transition-colors"
          >
            <Settings className="h-4 w-4 text-blue-600" />
            <div>
              <div className="font-medium text-gray-900">Metric Defaults Only</div>
              <div className="text-xs text-gray-500">Apply default metric mappings</div>
            </div>
            {isActionLoading('metrics') && (
              <div className="ml-auto animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full" />
            )}
          </button>

          <button
            onClick={() => handleAction('all', onApplyAllDefaults)}
            disabled={isActionLoading('all')}
            className="w-full px-4 py-2 text-left hover:bg-purple-50 flex items-center gap-3 transition-colors"
          >
            <Sparkles className="h-4 w-4 text-green-600" />
            <div>
              <div className="font-medium text-gray-900">All Defaults</div>
              <div className="text-xs text-gray-500">Apply both context and metric defaults</div>
            </div>
            {isActionLoading('all') && (
              <div className="ml-auto animate-spin h-4 w-4 border-2 border-green-600 border-t-transparent rounded-full" />
            )}
          </button>

          {(onAutoSuggestContexts || onAutoSuggestMetrics) && (
            <>
              <div className="border-t border-gray-200 my-2" />
              <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Auto-Suggest
              </div>

              {onAutoSuggestContexts && (
                <button
                  onClick={() => handleAction('suggest-contexts', onAutoSuggestContexts)}
                  disabled={isActionLoading('suggest-contexts')}
                  className="w-full px-4 py-2 text-left hover:bg-blue-50 flex items-center gap-3 transition-colors"
                >
                  <Wand2 className="h-4 w-4 text-purple-600" />
                  <div>
                    <div className="font-medium text-gray-900">Suggest Contexts</div>
                    <div className="text-xs text-gray-500">Auto-detect context column mappings</div>
                  </div>
                  {isActionLoading('suggest-contexts') && (
                    <div className="ml-auto animate-spin h-4 w-4 border-2 border-purple-600 border-t-transparent rounded-full" />
                  )}
                </button>
              )}

              {onAutoSuggestMetrics && (
                <button
                  onClick={() => handleAction('suggest-metrics', onAutoSuggestMetrics)}
                  disabled={isActionLoading('suggest-metrics')}
                  className="w-full px-4 py-2 text-left hover:bg-blue-50 flex items-center gap-3 transition-colors"
                >
                  <Wand2 className="h-4 w-4 text-blue-600" />
                  <div>
                    <div className="font-medium text-gray-900">Suggest Metrics</div>
                    <div className="text-xs text-gray-500">Auto-detect metric column mappings</div>
                  </div>
                  {isActionLoading('suggest-metrics') && (
                    <div className="ml-auto animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full" />
                  )}
                </button>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}
