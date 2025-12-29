import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Database, FileText, Calendar, HardDrive, Search, Filter, Eye, ArrowRight, X, Table } from 'lucide-react'
import { formatDate, formatBytes, cn } from '@/lib/utils'
import { useDataSets, useDataSetPreview, type DataSetRef } from '@/hooks/useDataSets'

const TOOL_FILTERS = [
  { value: '', label: 'All Tools' },
  { value: 'dat', label: 'Data Aggregator' },
  { value: 'sov', label: 'SOV Analyzer' },
  { value: 'pptx', label: 'PowerPoint Generator' },
]

const toolColors: Record<string, string> = {
  dat: 'bg-emerald-100 text-emerald-700',
  sov: 'bg-purple-100 text-purple-700',
  pptx: 'bg-orange-100 text-orange-700',
  manual: 'bg-slate-100 text-slate-600',
}

export function DatasetsPage() {
  const [toolFilter, setToolFilter] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [previewDatasetId, setPreviewDatasetId] = useState<string | null>(null)
  const navigate = useNavigate()

  const { data: datasets, isLoading, error } = useDataSets({
    tool: toolFilter || undefined,
    limit: 100,
  })

  // Filter by search query
  const filteredDatasets = datasets?.filter((ds) =>
    searchQuery === '' || 
    ds.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    ds.dataset_id.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const handlePipeTo = (datasetId: string, targetTool: 'pptx' | 'sov') => {
    navigate(`/tools/${targetTool}?input_datasets=${datasetId}`)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        Failed to load datasets. Make sure the gateway is running.
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">DataSets</h1>
        <span className="text-sm text-slate-500">
          {filteredDatasets?.length || 0} of {datasets?.length || 0} datasets
        </span>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search by name or ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>
        <div className="relative">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <select
            value={toolFilter}
            onChange={(e) => setToolFilter(e.target.value)}
            className="pl-10 pr-8 py-2 border border-slate-300 rounded-lg appearance-none bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          >
            {TOOL_FILTERS.map((filter) => (
              <option key={filter.value} value={filter.value}>
                {filter.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Dataset List */}
      {filteredDatasets?.length === 0 ? (
        <div className="bg-slate-50 border border-slate-200 rounded-lg p-8 text-center">
          <Database className="w-12 h-12 text-slate-400 mx-auto" />
          <h3 className="mt-4 text-lg font-medium text-slate-900">
            {datasets?.length === 0 ? 'No DataSets Yet' : 'No Matching DataSets'}
          </h3>
          <p className="mt-2 text-sm text-slate-600">
            {datasets?.length === 0
              ? 'DataSets will appear here when you export data from any tool.'
              : 'Try adjusting your search or filter criteria.'}
          </p>
        </div>
      ) : (
        <div className="grid gap-4">
          {filteredDatasets?.map((dataset) => (
            <DataSetRow
              key={dataset.dataset_id}
              dataset={dataset}
              onPreview={() => setPreviewDatasetId(dataset.dataset_id)}
              onPipeTo={handlePipeTo}
            />
          ))}
        </div>
      )}

      {/* Preview Modal */}
      {previewDatasetId && (
        <PreviewModal
          datasetId={previewDatasetId}
          onClose={() => setPreviewDatasetId(null)}
        />
      )}
    </div>
  )
}

interface DataSetRowProps {
  dataset: DataSetRef
  onPreview: () => void
  onPipeTo: (datasetId: string, tool: 'pptx' | 'sov') => void
}

function DataSetRow({ dataset, onPreview, onPipeTo }: DataSetRowProps) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-4 hover:border-slate-300 transition-colors">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h3 className="font-medium text-slate-900 truncate">{dataset.name}</h3>
            <span className={cn('text-xs px-2 py-0.5 rounded-full uppercase', toolColors[dataset.created_by_tool] || toolColors.manual)}>
              {dataset.created_by_tool}
            </span>
          </div>
          <p className="text-xs text-slate-500 font-mono mt-1">{dataset.dataset_id}</p>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-slate-500">
        <span className="flex items-center gap-1">
          <FileText className="w-3 h-3" />
          {dataset.row_count.toLocaleString()} rows × {dataset.column_count} cols
        </span>
        {dataset.size_bytes && (
          <span className="flex items-center gap-1">
            <HardDrive className="w-3 h-3" />
            {formatBytes(dataset.size_bytes)}
          </span>
        )}
        <span className="flex items-center gap-1">
          <Calendar className="w-3 h-3" />
          {formatDate(dataset.created_at)}
        </span>
      </div>

      {/* Actions */}
      <div className="mt-4 pt-3 border-t border-slate-100 flex flex-wrap gap-2">
        <button
          onClick={onPreview}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-600 bg-slate-50 hover:bg-slate-100 rounded-md transition-colors"
        >
          <Eye className="w-3 h-3" />
          Preview
        </button>
        <button
          onClick={() => onPipeTo(dataset.dataset_id, 'pptx')}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-orange-600 bg-orange-50 hover:bg-orange-100 rounded-md transition-colors"
        >
          <ArrowRight className="w-3 h-3" />
          Pipe to PPTX
        </button>
        {dataset.created_by_tool === 'dat' && (
          <button
            onClick={() => onPipeTo(dataset.dataset_id, 'sov')}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-purple-600 bg-purple-50 hover:bg-purple-100 rounded-md transition-colors"
          >
            <ArrowRight className="w-3 h-3" />
            Pipe to SOV
          </button>
        )}
      </div>
    </div>
  )
}

interface PreviewModalProps {
  datasetId: string
  onClose: () => void
}

function PreviewModal({ datasetId, onClose }: PreviewModalProps) {
  const { data: preview, isLoading, error } = useDataSetPreview(datasetId, 100)

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-4xl max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <div className="flex items-center gap-3">
            <Table className="w-5 h-5 text-slate-500" />
            <div>
              <h2 className="font-semibold text-slate-900">DataSet Preview</h2>
              <p className="text-xs text-slate-500 font-mono">{datasetId}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-slate-500" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          {isLoading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
            </div>
          ) : error ? (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
              Failed to load preview.
            </div>
          ) : preview ? (
            <div className="space-y-4">
              <div className="text-sm text-slate-500">
                Showing {preview.preview_rows} of {preview.total_rows.toLocaleString()} rows
              </div>
              <div className="overflow-x-auto border border-slate-200 rounded-lg">
                <table className="min-w-full divide-y divide-slate-200">
                  <thead className="bg-slate-50">
                    <tr>
                      {preview.columns.map((col: string) => (
                        <th
                          key={col}
                          className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider"
                        >
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-slate-200">
                    {preview.rows.map((row: Record<string, unknown>, i: number) => (
                      <tr key={i} className="hover:bg-slate-50">
                        {preview.columns.map((col: string) => (
                          <td key={col} className="px-4 py-2 text-sm text-slate-900 whitespace-nowrap">
                            {formatCellValue(row[col])}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  )
}

function formatCellValue(value: unknown): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'number') {
    return Number.isInteger(value) ? value.toString() : value.toFixed(4)
  }
  if (typeof value === 'object') {
    return JSON.stringify(value)
  }
  return String(value)
}
