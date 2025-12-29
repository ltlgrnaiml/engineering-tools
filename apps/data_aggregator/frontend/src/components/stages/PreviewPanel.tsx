import { useState } from 'react'
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
  const [hasLoadedPreview, setHasLoadedPreview] = useState(false)

  // Lock the Preview stage and optionally load preview data
  const lockMutation = useMutation({
    mutationFn: async (loadData: boolean = false) => {
      console.log('[PreviewPanel] Locking preview stage...')
      const response = await debugFetch(`/api/dat/runs/${runId}/stages/preview/lock`, {
        method: 'POST',
      })
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to lock stage' }))
        console.error('[PreviewPanel] Lock failed:', error)
        throw new Error(error.detail || 'Failed to lock stage')
      }
      const result = await response.json()
      console.log('[PreviewPanel] Lock success:', result)
      return { result, loadData }
    },
    onSuccess: ({ loadData }) => {
      queryClient.invalidateQueries({ queryKey: ['dat-preview-status', runId] })
      if (loadData) {
        // Now that stage is locked, fetch the preview data
        setHasLoadedPreview(true)
        queryClient.invalidateQueries({ queryKey: ['dat-preview', runId] })
      } else {
        // Skip mode - just refresh run status
        queryClient.invalidateQueries({ queryKey: ['dat-run', runId] })
      }
    },
    onError: (error) => {
      console.error('[PreviewPanel] Lock mutation error:', error)
    },
  })

  // Get stage status
  const { data: stageStatus, isLoading: statusLoading } = useQuery({
    queryKey: ['dat-preview-status', runId],
    queryFn: async () => {
      console.log('[PreviewPanel] Fetching stage status...')
      const response = await debugFetch(`/api/dat/runs/${runId}/stages/preview`)
      if (!response.ok) {
        console.log('[PreviewPanel] Stage status not found, treating as unlocked')
        return { state: 'unlocked' }
      }
      const result = await response.json()
      console.log('[PreviewPanel] Stage status:', result)
      return result
    },
  })

  // Fetch preview data (only when user clicks "Load Preview")
  const { data: preview, isLoading: previewLoading, error: previewError } = useQuery({
    queryKey: ['dat-preview', runId],
    queryFn: async (): Promise<PreviewData> => {
      console.log('[PreviewPanel] Fetching preview data...')
      const response = await debugFetch(`/api/dat/runs/${runId}/stages/preview/data?rows=50`)
      if (!response.ok) {
        const errorText = await response.text()
        console.error('[PreviewPanel] Preview data fetch failed:', errorText)
        throw new Error('Failed to fetch preview')
      }
      const result = await response.json()
      console.log('[PreviewPanel] Preview data:', result)
      return result
    },
    enabled: hasLoadedPreview || stageStatus?.state === 'locked',
    retry: 1,
  })

  // Handle loading preview - lock first, then data will load automatically
  const handleLoadPreview = () => {
    lockMutation.mutate(true)  // true = load data after lock
  }

  // Combined loading state
  const isLoading = statusLoading || (hasLoadedPreview && previewLoading) || lockMutation.isPending

  // Combined error state  
  const error = previewError || lockMutation.error

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Data Preview</h2>
        <p className="text-slate-600 mt-1">Review a sample of the data before parsing.</p>
      </div>

      {/* Initial Choice - Load Preview or Skip */}
      {!hasLoadedPreview && !preview && stageStatus?.state !== 'locked' && (
        <div className="bg-white rounded-lg border border-slate-200 p-8 text-center">
          <Eye className="w-12 h-12 mx-auto mb-4 text-slate-300" />
          <h3 className="text-lg font-medium text-slate-900 mb-2">Preview Your Data</h3>
          <p className="text-slate-600 mb-6 max-w-md mx-auto">
            This optional step lets you review a sample of your data before parsing. 
            You can skip this step if you're confident in your table selections.
          </p>
          <div className="flex justify-center gap-4">
            <button
              onClick={() => lockMutation.mutate(false)}
              disabled={lockMutation.isPending}
              className="px-6 py-3 border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg font-medium transition-colors"
            >
              Skip Preview →
            </button>
            <button
              onClick={handleLoadPreview}
              disabled={previewLoading}
              className="px-6 py-3 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
            >
              {previewLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Eye className="w-5 h-5" />
              )}
              Load Preview
            </button>
          </div>
        </div>
      )}

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
                setHasLoadedPreview(false)
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

      {/* Loading State */}
      {isLoading && hasLoadedPreview && (
        <div className="bg-white rounded-lg border border-slate-200 p-8">
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
            <span className="ml-2 text-slate-500">Loading preview...</span>
          </div>
        </div>
      )}

      {/* Preview Data */}
      {(preview || stageStatus?.state === 'locked') && !isLoading && !error && (
        <>
          {/* Stats */}
          {preview && (
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
            {preview ? (
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

          {/* Actions - mark preview complete to advance to Parse */}
          <div className="flex justify-end gap-3">
            <button
              onClick={async () => {
                try {
                  const response = await debugFetch(`/api/dat/runs/${runId}/stages/preview/complete`, {
                    method: 'POST',
                  })
                  if (response.ok) {
                    queryClient.invalidateQueries({ queryKey: ['dat-run', runId] })
                  }
                } catch (error) {
                  console.error('Failed to complete preview:', error)
                }
              }}
              className="px-6 py-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg font-medium transition-colors"
            >
              Continue to Parse
            </button>
          </div>
        </>
      )}
    </div>
  )
}
