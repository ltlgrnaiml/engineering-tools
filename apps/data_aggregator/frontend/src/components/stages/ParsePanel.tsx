import { useState, useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Play, Square, CheckCircle2, Loader2, AlertCircle } from 'lucide-react'

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
  const queryClient = useQueryClient()

  const { data: progress, refetch } = useQuery({
    queryKey: ['dat-parse-progress', runId],
    queryFn: async (): Promise<ParseProgress> => {
      const response = await fetch(`/api/dat/runs/${runId}/stages/parse/progress`)
      if (!response.ok) throw new Error('Failed to fetch progress')
      return response.json()
    },
    refetchInterval: isPolling ? 1000 : false,
  })

  useEffect(() => {
    if (progress?.status === 'running') {
      setIsPolling(true)
    } else {
      setIsPolling(false)
    }
  }, [progress?.status])

  const startMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch(`/api/dat/runs/${runId}/stages/parse/start`, {
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
      const response = await fetch(`/api/dat/runs/${runId}/stages/parse/lock`, {
        method: 'POST',
      })
      if (!response.ok) throw new Error('Failed to lock stage')
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dat-run', runId] })
    },
  })

  const status = progress?.status || 'idle'

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Parse Data</h2>
        <p className="text-slate-600 mt-1">Extract and combine data from selected tables.</p>
      </div>

      {/* Progress Card */}
      <div className="bg-white rounded-lg border border-slate-200 p-6">
        {status === 'idle' && (
          <div className="text-center py-8">
            <Play className="w-12 h-12 mx-auto mb-4 text-slate-300" />
            <h3 className="text-lg font-medium text-slate-900 mb-2">Ready to Parse</h3>
            <p className="text-slate-600 mb-6">
              Click the button below to start extracting data from the selected tables.
            </p>
            <button
              onClick={() => startMutation.mutate()}
              disabled={startMutation.isPending}
              className="px-6 py-3 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
            >
              {startMutation.isPending ? (
                <Loader2 className="w-5 h-5 animate-spin inline mr-2" />
              ) : (
                <Play className="w-5 h-5 inline mr-2" />
              )}
              Start Parsing
            </button>
          </div>
        )}

        {status === 'running' && progress && (
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

        {status === 'completed' && progress && (
          <div className="text-center py-8">
            <CheckCircle2 className="w-12 h-12 mx-auto mb-4 text-emerald-500" />
            <h3 className="text-lg font-medium text-slate-900 mb-2">Parsing Complete!</h3>
            <p className="text-slate-600">
              Successfully processed {progress.processed_rows.toLocaleString()} rows 
              from {progress.processed_files} files.
            </p>
          </div>
        )}

        {status === 'failed' && progress && (
          <div className="text-center py-8">
            <AlertCircle className="w-12 h-12 mx-auto mb-4 text-red-500" />
            <h3 className="text-lg font-medium text-slate-900 mb-2">Parsing Failed</h3>
            <p className="text-red-600 mb-4">{progress.error || 'An error occurred during parsing.'}</p>
            <button
              onClick={() => startMutation.mutate()}
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
      {status === 'completed' && (
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
