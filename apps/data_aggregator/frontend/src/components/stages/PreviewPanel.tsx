import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Eye, Loader2 } from 'lucide-react'
import { useDebugFetch } from '../debug'

interface PreviewPanelProps {
  runId: string
}

interface PreviewData {
  columns: string[]
  rows: Record<string, unknown>[]
  total_rows: number
  sampled: boolean
}

export function PreviewPanel({ runId }: PreviewPanelProps) {
  const queryClient = useQueryClient()
  const debugFetch = useDebugFetch()

  const { data: preview, isLoading } = useQuery({
    queryKey: ['dat-preview', runId],
    queryFn: async (): Promise<PreviewData> => {
      const response = await debugFetch(`/api/dat/runs/${runId}/stages/preview/data?limit=50`)
      if (!response.ok) throw new Error('Failed to fetch preview')
      return response.json()
    },
  })

  const lockMutation = useMutation({
    mutationFn: async () => {
      const response = await debugFetch(`/api/dat/runs/${runId}/stages/preview/lock`, {
        method: 'POST',
      })
      if (!response.ok) throw new Error('Failed to lock stage')
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dat-run', runId] })
    },
  })

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Data Preview</h2>
        <p className="text-slate-600 mt-1">Review a sample of the data before parsing.</p>
      </div>

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
          {preview.sampled && (
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
