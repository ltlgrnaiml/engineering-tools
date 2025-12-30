import { useState, useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Play, Square, CheckCircle2, Loader2, AlertCircle, Table, Info } from 'lucide-react'
import { useDebugFetch } from '../debug'
import { useExtractionFlow } from '../../hooks/useProfiles'
import type { ExtractionResponse, ContextInfo } from '../../types/profile'

interface ParsePanelProps {
  runId: string
}

interface ParseProgress {
  status: 'idle' | 'running' | 'completed' | 'cancelled' | 'failed'
  progress: number
  current_file?: string
  processed_files: number
  total_files: number
  processed_rows: number
  error?: string
}

export function ParsePanel({ runId }: ParsePanelProps) {
  const [isPolling, setIsPolling] = useState(false)
  const [extractionResult, setExtractionResult] = useState<ExtractionResponse | null>(null)
  const queryClient = useQueryClient()
  const debugFetch = useDebugFetch()

  // Get run state to check if profile-based
  const { data: runState } = useQuery({
    queryKey: ['dat-run', runId],
    queryFn: async () => {
      const response = await debugFetch(`/api/dat/runs/${runId}`)
      if (!response.ok) throw new Error('Failed to fetch run')
      return response.json()
    },
  })

  const profileId = runState?.profile_id
  const useProfileExtraction = !!profileId

  // Profile extraction flow
  const { extraction, isExtracting } = useExtractionFlow(runId)

  // Legacy progress-based polling for non-profile extraction
  const { data: progress, refetch } = useQuery({
    queryKey: ['dat-parse-progress', runId],
    queryFn: async (): Promise<ParseProgress> => {
      const response = await debugFetch(`/api/dat/runs/${runId}/stages/parse/progress`)
      if (!response.ok) throw new Error('Failed to fetch progress')
      return response.json()
    },
    refetchInterval: isPolling ? 1000 : false,
    enabled: !useProfileExtraction,
  })

  useEffect(() => {
    if (progress?.status === 'running') {
      setIsPolling(true)
    } else {
      setIsPolling(false)
    }
  }, [progress?.status])

  // Profile-based extraction mutation
  const handleProfileExtract = async () => {
    try {
      const result = await extraction.mutateAsync(undefined)
      setExtractionResult(result)
    } catch (error) {
      console.error('Profile extraction failed:', error)
    }
  }

  // Legacy start mutation for non-profile extraction
  const startMutation = useMutation({
    mutationFn: async () => {
      const response = await debugFetch(`/api/dat/runs/${runId}/stages/parse/start`, {
        method: 'POST',
      })
      if (!response.ok) throw new Error('Failed to start parse')
      return response.json()
    },
    onSuccess: () => {
      setIsPolling(true)
      refetch()
    },
  })

  const cancelMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch(`/api/dat/runs/${runId}/stages/parse/cancel`, {
        method: 'POST',
      })
      if (!response.ok) throw new Error('Failed to cancel parse')
      return response.json()
    },
    onSuccess: () => {
      refetch()
    },
  })

  const lockMutation = useMutation({
    mutationFn: async () => {
      const response = await debugFetch(`/api/dat/runs/${runId}/stages/parse/lock`, {
        method: 'POST',
      })
      if (!response.ok) throw new Error('Failed to lock stage')
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dat-run', runId] })
    },
  })

  const status = useProfileExtraction
    ? (extractionResult ? 'completed' : (isExtracting ? 'running' : 'idle'))
    : (progress?.status || 'idle')

  const isCompleted = status === 'completed'

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Parse Data</h2>
        <p className="text-slate-600 mt-1">
          {useProfileExtraction
            ? 'Execute profile-driven extraction on selected tables.'
            : 'Extract and combine data from selected tables.'}
        </p>
      </div>

      {/* Progress Card */}
      <div className="bg-white rounded-lg border border-slate-200 p-6">
        {status === 'idle' && (
          <div className="text-center py-8">
            <Play className="w-12 h-12 mx-auto mb-4 text-slate-300" />
            <h3 className="text-lg font-medium text-slate-900 mb-2">Ready to Extract</h3>
            <p className="text-slate-600 mb-6">
              {useProfileExtraction
                ? 'Click below to run profile-driven extraction. Tables and context will be kept separate.'
                : 'Click the button below to start extracting data from the selected tables.'}
            </p>
            <button
              onClick={useProfileExtraction ? handleProfileExtract : () => startMutation.mutate()}
              disabled={isExtracting || startMutation.isPending}
              className="px-6 py-3 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
            >
              {(isExtracting || startMutation.isPending) ? (
                <Loader2 className="w-5 h-5 animate-spin inline mr-2" />
              ) : (
                <Play className="w-5 h-5 inline mr-2" />
              )}
              {useProfileExtraction ? 'Run Profile Extraction' : 'Start Parsing'}
            </button>
          </div>
        )}

        {status === 'running' && !useProfileExtraction && progress && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Loader2 className="w-5 h-5 animate-spin text-emerald-500" />
                <span className="font-medium text-slate-900">Parsing in progress...</span>
              </div>
              <button
                onClick={() => cancelMutation.mutate()}
                disabled={cancelMutation.isPending}
                className="px-4 py-2 bg-red-100 hover:bg-red-200 text-red-700 rounded-lg text-sm font-medium transition-colors"
              >
                <Square className="w-4 h-4 inline mr-1" />
                Cancel
              </button>
            </div>

            {/* Progress Bar */}
            <div>
              <div className="flex justify-between text-sm text-slate-600 mb-1">
                <span>{progress.current_file || 'Processing...'}</span>
                <span>{Math.round(progress.progress)}%</span>
              </div>
              <div className="w-full h-3 bg-slate-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-emerald-500 transition-all duration-300"
                  style={{ width: `${progress.progress}%` }}
                />
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4 pt-2">
              <div className="text-center">
                <div className="text-2xl font-semibold text-slate-900">
                  {progress.processed_files}/{progress.total_files}
                </div>
                <div className="text-sm text-slate-600">Files</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-semibold text-slate-900">
                  {progress.processed_rows.toLocaleString()}
                </div>
                <div className="text-sm text-slate-600">Rows Processed</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-semibold text-slate-900">
                  {Math.round(progress.progress)}%
                </div>
                <div className="text-sm text-slate-600">Complete</div>
              </div>
            </div>
          </div>
        )}

        {status === 'running' && useProfileExtraction && (
          <div className="text-center py-8">
            <Loader2 className="w-12 h-12 mx-auto mb-4 animate-spin text-emerald-500" />
            <h3 className="text-lg font-medium text-slate-900 mb-2">Extracting...</h3>
            <p className="text-slate-600">Running profile-driven extraction on selected files.</p>
          </div>
        )}

        {/* Profile Extraction Result */}
        {isCompleted && useProfileExtraction && extractionResult && (
          <div className="space-y-6">
            <div className="text-center py-4">
              <CheckCircle2 className="w-12 h-12 mx-auto mb-4 text-emerald-500" />
              <h3 className="text-lg font-medium text-slate-900 mb-2">Extraction Complete!</h3>
              <p className="text-slate-600">
                Successfully extracted {extractionResult.tables_extracted} tables.
              </p>
            </div>

            {/* Extracted Tables Summary */}
            <div className="bg-slate-50 rounded-lg p-4">
              <h4 className="font-medium text-slate-900 mb-3 flex items-center gap-2">
                <Table className="w-4 h-4" />
                Extracted Tables
              </h4>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(extractionResult.table_details).map(([tableId, details]) => (
                  <div
                    key={tableId}
                    className="bg-white rounded border border-slate-200 p-3"
                  >
                    <div className="font-medium text-slate-900 text-sm">{tableId}</div>
                    <div className="text-xs text-slate-500 mt-1">
                      {details.row_count.toLocaleString()} rows × {details.column_count} cols
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Context Information */}
            <ContextInfoPanel context={extractionResult.context} />

            {/* Validation Warnings */}
            {extractionResult.validation_warnings.length > 0 && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                <h4 className="font-medium text-amber-800 mb-2 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4" />
                  Validation Warnings
                </h4>
                <ul className="text-sm text-amber-700 space-y-1">
                  {extractionResult.validation_warnings.map((warning, i) => (
                    <li key={i}>• {warning}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Legacy completion state */}
        {isCompleted && !useProfileExtraction && progress && progress.processed_rows !== undefined && (
          <div className="text-center py-8">
            <CheckCircle2 className="w-12 h-12 mx-auto mb-4 text-emerald-500" />
            <h3 className="text-lg font-medium text-slate-900 mb-2">Parsing Complete!</h3>
            <p className="text-slate-600">
              Successfully processed {progress.processed_rows.toLocaleString()} rows 
              from {progress.processed_files} files.
            </p>
          </div>
        )}

        {status === 'failed' && (
          <div className="text-center py-8">
            <AlertCircle className="w-12 h-12 mx-auto mb-4 text-red-500" />
            <h3 className="text-lg font-medium text-slate-900 mb-2">Extraction Failed</h3>
            <p className="text-red-600 mb-4">
              {extraction.error?.message || progress?.error || 'An error occurred during extraction.'}
            </p>
            <button
              onClick={useProfileExtraction ? handleProfileExtract : () => startMutation.mutate()}
              className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg font-medium"
            >
              Try Again
            </button>
          </div>
        )}

        {status === 'cancelled' && (
          <div className="text-center py-8">
            <Square className="w-12 h-12 mx-auto mb-4 text-amber-500" />
            <h3 className="text-lg font-medium text-slate-900 mb-2">Parsing Cancelled</h3>
            <p className="text-slate-600 mb-4">
              The parsing operation was cancelled. Partial results may be available.
            </p>
            <button
              onClick={() => startMutation.mutate()}
              className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg font-medium"
            >
              Start Over
            </button>
          </div>
        )}
      </div>

      {/* Actions */}
      {isCompleted && (
        <div className="flex justify-end gap-3">
          <button
            onClick={() => lockMutation.mutate()}
            disabled={lockMutation.isPending}
            className="px-6 py-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
          >
            {lockMutation.isPending ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              'Continue to Export'
            )}
          </button>
        </div>
      )}
    </div>
  )
}

/**
 * Component to display extracted context information.
 * Per DESIGN §4, §9: Shows separated context for transparency.
 */
function ContextInfoPanel({ context }: { context: ContextInfo }) {
  const hasRunContext = context.available_run_keys.length > 0
  const hasImageContext = context.available_image_keys.length > 0

  if (!hasRunContext && !hasImageContext) {
    return null
  }

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
      <h4 className="font-medium text-blue-900 mb-3 flex items-center gap-2">
        <Info className="w-4 h-4" />
        Extracted Context (Stored Separately)
      </h4>
      <p className="text-xs text-blue-700 mb-3">
        Context is extracted separately from tables. Your selected context options will be applied during export.
      </p>
      
      <div className="space-y-3">
        {hasRunContext && (
          <div>
            <div className="text-sm font-medium text-blue-900 mb-1">Run-Level Context</div>
            <div className="flex flex-wrap gap-1">
              {context.available_run_keys.map(key => (
                <span
                  key={key}
                  className="px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded"
                >
                  {key}: {String(context.run_context[key] ?? '—')}
                </span>
              ))}
            </div>
          </div>
        )}
        
        {hasImageContext && (
          <div>
            <div className="text-sm font-medium text-blue-900 mb-1">
              Image-Level Context ({Object.keys(context.image_contexts).length} images)
            </div>
            <div className="text-xs text-blue-700">
              Available keys: {context.available_image_keys.join(', ')}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
