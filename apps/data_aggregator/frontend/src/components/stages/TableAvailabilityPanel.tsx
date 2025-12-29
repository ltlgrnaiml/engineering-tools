import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Table, CheckCircle2, XCircle, Loader2 } from 'lucide-react'
import { useDebugFetch } from '../debug'

interface TableAvailabilityPanelProps {
  runId: string
}

interface TableInfo {
  name: string
  file: string
  available: boolean
  row_count?: number
  column_count?: number
}

export function TableAvailabilityPanel({ runId }: TableAvailabilityPanelProps) {
  const queryClient = useQueryClient()
  const debugFetch = useDebugFetch()

  const { data: tables, isLoading } = useQuery({
    queryKey: ['dat-tables', runId],
    queryFn: async (): Promise<TableInfo[]> => {
      const response = await debugFetch(`/api/dat/runs/${runId}/stages/table_availability/scan`)
      if (!response.ok) throw new Error('Failed to scan tables')
      return response.json()
    },
  })

  const lockMutation = useMutation({
    mutationFn: async () => {
      const response = await debugFetch(`/api/dat/runs/${runId}/stages/table_availability/lock`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
      if (!response.ok) throw new Error('Failed to lock stage')
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dat-run', runId] })
    },
  })

  const availableCount = tables?.filter(t => t.available).length || 0
  const totalCount = tables?.length || 0

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Table Availability</h2>
        <p className="text-slate-600 mt-1">Review detected tables and their availability status.</p>
      </div>

      {/* Summary */}
      <div className="bg-white rounded-lg border border-slate-200 p-4">
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <div className="text-2xl font-semibold text-slate-900">{availableCount} / {totalCount}</div>
            <div className="text-sm text-slate-600">tables available</div>
          </div>
          <div className="w-32 h-2 bg-slate-200 rounded-full overflow-hidden">
            <div 
              className="h-full bg-emerald-500 transition-all"
              style={{ width: `${totalCount > 0 ? (availableCount / totalCount) * 100 : 0}%` }}
            />
          </div>
        </div>
      </div>

      {/* Table List */}
      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="text-left px-4 py-3 text-sm font-medium text-slate-600">Status</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-slate-600">Table</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-slate-600">File</th>
                <th className="text-right px-4 py-3 text-sm font-medium text-slate-600">Rows</th>
                <th className="text-right px-4 py-3 text-sm font-medium text-slate-600">Columns</th>
              </tr>
            </thead>
            <tbody>
              {tables?.map((table) => (
                <tr key={`${table.file}:${table.name}`} className="border-b border-slate-100 last:border-0">
                  <td className="px-4 py-3">
                    {table.available ? (
                      <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                    ) : (
                      <XCircle className="w-5 h-5 text-red-400" />
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <Table className="w-4 h-4 text-slate-400" />
                      <span className="font-medium text-slate-900">{table.name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-600 truncate max-w-xs">{table.file}</td>
                  <td className="px-4 py-3 text-right text-sm text-slate-600">
                    {table.row_count?.toLocaleString() || '-'}
                  </td>
                  <td className="px-4 py-3 text-right text-sm text-slate-600">
                    {table.column_count || '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-3">
        <button
          onClick={() => lockMutation.mutate()}
          disabled={availableCount === 0 || lockMutation.isPending}
          className="px-6 py-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
        >
          {lockMutation.isPending ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            'Continue'
          )}
        </button>
      </div>
    </div>
  )
}
