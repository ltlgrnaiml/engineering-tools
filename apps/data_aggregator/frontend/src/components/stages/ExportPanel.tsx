import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Download, Database, Presentation, BarChart3, Loader2, CheckCircle2 } from 'lucide-react'
import { useDebugFetch } from '../debug'

interface ExportPanelProps {
  runId: string
}

interface ExportSummary {
  row_count: number
  column_count: number
  columns: string[]
  aggregation_levels: string[]
}

export function ExportPanel({ runId }: ExportPanelProps) {
  const [datasetName, setDatasetName] = useState('')
  const [exportedDatasetId, setExportedDatasetId] = useState<string | null>(null)
  const queryClient = useQueryClient()
  const debugFetch = useDebugFetch()

  const { data: summary, isLoading } = useQuery({
    queryKey: ['dat-export-summary', runId],
    queryFn: async (): Promise<ExportSummary> => {
      const response = await debugFetch(`/api/dat/runs/${runId}/stages/export/summary`)
      if (!response.ok) throw new Error('Failed to fetch summary')
      return response.json()
    },
  })

  const exportMutation = useMutation({
    mutationFn: async () => {
      const response = await debugFetch(`/api/dat/runs/${runId}/stages/export/lock`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: datasetName || `DAT Export ${new Date().toISOString().split('T')[0]}` }),
      })
      if (!response.ok) throw new Error('Failed to export dataset')
      return response.json()
    },
    onSuccess: (data) => {
      setExportedDatasetId(data.dataset_id)
      queryClient.invalidateQueries({ queryKey: ['dat-run', runId] })
    },
  })

  if (exportedDatasetId) {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg border border-slate-200 p-8 text-center">
          <CheckCircle2 className="w-16 h-16 mx-auto mb-4 text-emerald-500" />
          <h2 className="text-2xl font-semibold text-slate-900 mb-2">Export Complete!</h2>
          <p className="text-slate-600 mb-6">
            Your data has been exported as a DataSet and is ready for use in other tools.
          </p>
          
          <div className="bg-slate-50 rounded-lg p-4 mb-6">
            <div className="text-sm text-slate-500 mb-1">Dataset ID</div>
            <code className="text-slate-900 font-mono">{exportedDatasetId}</code>
          </div>

          <div className="flex justify-center gap-3">
            <a
              href={`/datasets/${exportedDatasetId}`}
              className="inline-flex items-center gap-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg font-medium transition-colors"
            >
              <Database className="w-4 h-4" />
              View Dataset
            </a>
            <a
              href={`/tools/sov?dataset=${exportedDatasetId}`}
              className="inline-flex items-center gap-2 px-4 py-2 bg-purple-500 hover:bg-purple-600 text-white rounded-lg font-medium transition-colors"
            >
              <BarChart3 className="w-4 h-4" />
              Analyze with SOV
            </a>
            <a
              href={`/tools/pptx?dataset=${exportedDatasetId}`}
              className="inline-flex items-center gap-2 px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-lg font-medium transition-colors"
            >
              <Presentation className="w-4 h-4" />
              Generate Report
            </a>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Export DataSet</h2>
        <p className="text-slate-600 mt-1">Save the aggregated data as a DataSet for use in other tools.</p>
      </div>

      {/* Summary */}
      {isLoading ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
        </div>
      ) : summary && (
        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <h3 className="font-medium text-slate-900 mb-4">Export Summary</h3>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <div className="text-2xl font-semibold text-slate-900">
                {summary.row_count.toLocaleString()}
              </div>
              <div className="text-sm text-slate-600">Total Rows</div>
            </div>
            <div>
              <div className="text-2xl font-semibold text-slate-900">
                {summary.column_count}
              </div>
              <div className="text-sm text-slate-600">Columns</div>
            </div>
            <div>
              <div className="text-2xl font-semibold text-slate-900">
                {summary.aggregation_levels.length}
              </div>
              <div className="text-sm text-slate-600">Aggregation Levels</div>
            </div>
          </div>
          
          {summary.aggregation_levels.length > 0 && (
            <div className="mt-4 pt-4 border-t border-slate-100">
              <div className="text-sm text-slate-500 mb-2">Aggregation Levels</div>
              <div className="flex gap-2">
                {summary.aggregation_levels.map(level => (
                  <span key={level} className="px-2 py-1 bg-emerald-100 text-emerald-800 text-sm rounded">
                    {level}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Dataset Name */}
      <div className="bg-white rounded-lg border border-slate-200 p-4">
        <label className="block text-sm font-medium text-slate-700 mb-2">
          DataSet Name
        </label>
        <input
          type="text"
          value={datasetName}
          onChange={(e) => setDatasetName(e.target.value)}
          placeholder="Enter a name for this dataset..."
          className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
        />
      </div>

      {/* Export Actions */}
      <div className="flex justify-end gap-3">
        <button
          onClick={() => exportMutation.mutate()}
          disabled={exportMutation.isPending}
          className="px-6 py-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50 inline-flex items-center gap-2"
        >
          {exportMutation.isPending ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Download className="w-5 h-5" />
          )}
          Export DataSet
        </button>
      </div>
    </div>
  )
}
