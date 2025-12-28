import { useEffect, useRef, useCallback } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Eye, Loader2, AlertCircle, RefreshCw } from 'lucide-react'
import { useDebugFetch } from '../debug'

interface PreviewPanelProps {
  runId: string
}

interface PreviewData {
  columns: string[]
  rows: Record<string, unknown>[]
  total_rows: number
  row_count?: number
}

export function PreviewPanel({ runId }: PreviewPanelProps) {
  const queryClient = useQueryClient()
  const debugFetch = useDebugFetch()

  // Track if we've already attempted auto-lock to prevent infinite loops
  const autoLockAttempted = useRef(false)

  // First, lock the Preview stage to generate preview data from selected tables
  const lockMutation = useMutation({
    mutationFn: async () => {
      console.log('[PreviewPanel] Locking preview stage...')
      const response = await debugFetch(`/api/dat/v1/runs/${runId}/stages/preview/lock`, {
        method: 'POST',
      })
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to lock stage' }))
        console.error('[PreviewPanel] Lock failed:', error)
        throw new Error(error.detail || 'Failed to lock stage')
      }
      const result = await response.json()
      console.log('[PreviewPanel] Lock success:', result)
      return result
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dat-preview', runId] })
      queryClient.invalidateQueries({ queryKey: ['dat-run', runId] })
    },
    onError: (error) => {
      console.error('[PreviewPanel] Lock mutation error:', error)
    },
  })

  // Get stage status to determine if we need to auto-lock
  const { data: stageStatus, isLoading: statusLoading, error: statusError } = useQuery({
    queryKey: ['dat-preview-status', runId],
    queryFn: async () => {
      console.log('[PreviewPanel] Fetching stage status...')
      const response = await debugFetch(`/api/dat/v1/runs/${runId}/stages/preview`)
      if (!response.ok) {
        console.log('[PreviewPanel] Stage status not found, treating as unlocked')
        return { state: 'unlocked' }
      }
      const result = await response.json()
      console.log('[PreviewPanel] Stage status:', result)
      return result
    },
  })

  // Auto-lock callback
  const attemptAutoLock = useCallback(() => {
    if (stageStatus?.state === 'unlocked' && !autoLockAttempted.current && !lockMutation.isPending) {
      console.log('[PreviewPanel] Auto-locking preview stage')
      autoLockAttempted.current = true
      lockMutation.mutate()
    }
  }, [stageStatus?.state, lockMutation])

  // Auto-lock Preview stage on mount if not already locked
  useEffect(() => {
    attemptAutoLock()
  }, [attemptAutoLock])

  // Fetch preview data
  const { data: preview, isLoading: previewLoading, error: previewError } = useQuery({
    queryKey: ['dat-preview', runId],
    queryFn: async (): Promise<PreviewData> => {
      console.log('[PreviewPanel] Fetching preview data...')
      const response = await debugFetch(`/api/dat/v1/runs/${runId}/stages/preview/data?rows=50`)
      if (!response.ok) {
        const errorText = await response.text()
        console.error('[PreviewPanel] Preview data fetch failed:', errorText)
        throw new Error('Failed to fetch preview')
      }
      const result = await response.json()
      console.log('[PreviewPanel] Preview data:', result)
      return result
    },
    enabled: stageStatus?.state === 'locked' || lockMutation.isSuccess,
    retry: 1,
  })

  // Combined loading state
  const isLoading = statusLoading || previewLoading || lockMutation.isPending

  // Combined error state
  const error = statusError || previewError || lockMutation.error

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Data Preview</h2>
        <p className="text-slate-600 mt-1">Review a sample of the data before parsing.</p>
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-red-800 font-medium">Failed to load preview</p>
            <p className="text-red-600 text-sm mt-1">
              {error instanceof Error ? error.message : 'An unexpected error occurred'}
            </p>
            <button
              onClick={() => {
                autoLockAttempted.current = false
                queryClient.invalidateQueries({ queryKey: ['dat-preview-status', runId] })
              }}
              className="mt-2 flex items-center gap-2 text-sm text-red-700 hover:text-red-800 font-medium"
            >
              <RefreshCw className="w-4 h-4" />
              Retry
            </button>
          </div>
        </div>
      )}

      {/* Stats */}
      {preview && !error && (
        <div className="flex items-center gap-6 text-sm">
          <div>
            <span className="text-slate-500">Total Rows:</span>{' '}
            <span className="font-medium text-slate-900">{preview.total_rows.toLocaleString()}</span>
          </div>
          <div>
            <span className="text-slate-500">Columns:</span>{' '}
            <span className="font-medium text-slate-900">{preview.columns.length}</span>
          </div>
          {preview.rows.length < preview.total_rows && (
            <div className="text-amber-600">
              <Eye className="w-4 h-4 inline mr-1" />
              Showing sample of {preview.rows.length} rows
            </div>
          )}
        </div>
      )}

      {/* Data Table */}
      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
            <span className="ml-2 text-slate-500">Loading preview...</span>
          </div>
        ) : error ? (
          <div className="text-center py-12 text-slate-500">
            Unable to load preview data
          </div>
        ) : preview ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  {preview.columns.map((col) => (
                    <th 
                      key={col} 
                      className="text-left px-3 py-2 font-medium text-slate-600 whitespace-nowrap"
                    >
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {preview.rows.map((row, idx) => (
                  <tr key={idx} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
                    {preview.columns.map((col) => (
                      <td key={col} className="px-3 py-2 text-slate-700 whitespace-nowrap">
                        {String(row[col] ?? '')}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12 text-slate-500">
            No preview data available
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-3">
        <button
          onClick={() => lockMutation.mutate()}
          disabled={!preview || lockMutation.isPending}
          className="px-6 py-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
        >
          {lockMutation.isPending ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            'Continue to Parse'
          )}
        </button>
      </div>
    </div>
  )
}
