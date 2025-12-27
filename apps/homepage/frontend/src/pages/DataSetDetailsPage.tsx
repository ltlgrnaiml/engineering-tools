import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { 
  ArrowLeft, 
  Database, 
  Calendar, 
  FileText, 
  Columns, 
  GitBranch,
  Presentation,
  BarChart3,
  Download,
  Loader2
} from 'lucide-react'
import { formatDate } from '@/lib/utils'

interface ColumnMeta {
  name: string
  dtype: string
  nullable?: boolean
  description?: string
}

interface DataSetManifest {
  dataset_id: string
  name: string
  created_at: string
  created_by_tool: 'dat' | 'sov' | 'pptx' | 'manual'
  columns: ColumnMeta[]
  row_count: number
  parent_dataset_ids: string[]
  aggregation_levels?: string[]
  description?: string
}

interface DataSetPreview {
  columns: string[]
  rows: Record<string, unknown>[]
  total_rows: number
}

async function fetchDataSetManifest(id: string): Promise<DataSetManifest> {
  const response = await fetch(`/api/datasets/v1/${id}`)
  if (!response.ok) throw new Error('Failed to fetch dataset')
  return response.json()
}

async function fetchDataSetPreview(id: string): Promise<DataSetPreview> {
  const response = await fetch(`/api/datasets/v1/${id}/preview?limit=20`)
  if (!response.ok) throw new Error('Failed to fetch preview')
  return response.json()
}

async function fetchDataSetLineage(id: string): Promise<{ parents: DataSetManifest[], children: DataSetManifest[] }> {
  const response = await fetch(`/api/datasets/v1/${id}/lineage`)
  if (!response.ok) throw new Error('Failed to fetch lineage')
  return response.json()
}

const toolColors: Record<string, string> = {
  dat: 'bg-emerald-100 text-emerald-800',
  sov: 'bg-purple-100 text-purple-800',
  pptx: 'bg-orange-100 text-orange-800',
  manual: 'bg-slate-100 text-slate-800',
}

export function DataSetDetailsPage() {
  const { id } = useParams<{ id: string }>()

  const { data: manifest, isLoading: manifestLoading, error: manifestError } = useQuery({
    queryKey: ['dataset', id],
    queryFn: () => fetchDataSetManifest(id!),
    enabled: !!id,
  })

  const { data: preview, isLoading: previewLoading } = useQuery({
    queryKey: ['dataset-preview', id],
    queryFn: () => fetchDataSetPreview(id!),
    enabled: !!id,
  })

  const { data: lineage } = useQuery({
    queryKey: ['dataset-lineage', id],
    queryFn: () => fetchDataSetLineage(id!),
    enabled: !!id,
  })

  if (manifestLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    )
  }

  if (manifestError || !manifest) {
    return (
      <div className="text-center py-16">
        <Database className="w-12 h-12 mx-auto mb-4 text-slate-300" />
        <h2 className="text-xl font-semibold text-slate-900">Dataset Not Found</h2>
        <p className="mt-2 text-slate-600">The requested dataset could not be found.</p>
        <Link to="/datasets" className="mt-4 inline-block text-primary-600 hover:text-primary-700">
          ← Back to Datasets
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <Link 
            to="/datasets" 
            className="inline-flex items-center gap-1 text-sm text-slate-600 hover:text-slate-900 mb-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Datasets
          </Link>
          <h1 className="text-2xl font-bold text-slate-900">{manifest.name}</h1>
          {manifest.description && (
            <p className="mt-1 text-slate-600">{manifest.description}</p>
          )}
        </div>
        <div className="flex gap-2">
          <Link
            to={`/tools/sov?dataset=${id}`}
            className="inline-flex items-center gap-2 px-4 py-2 bg-purple-500 hover:bg-purple-600 text-white rounded-lg text-sm font-medium transition-colors"
          >
            <BarChart3 className="w-4 h-4" />
            Analyze with SOV
          </Link>
          <Link
            to={`/tools/pptx?dataset=${id}`}
            className="inline-flex items-center gap-2 px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-lg text-sm font-medium transition-colors"
          >
            <Presentation className="w-4 h-4" />
            Generate Report
          </Link>
        </div>
      </div>

      {/* Metadata Cards */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <div className="flex items-center gap-2 text-slate-600 text-sm mb-1">
            <FileText className="w-4 h-4" />
            Rows
          </div>
          <div className="text-2xl font-semibold text-slate-900">
            {manifest.row_count.toLocaleString()}
          </div>
        </div>
        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <div className="flex items-center gap-2 text-slate-600 text-sm mb-1">
            <Columns className="w-4 h-4" />
            Columns
          </div>
          <div className="text-2xl font-semibold text-slate-900">
            {manifest.columns.length}
          </div>
        </div>
        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <div className="flex items-center gap-2 text-slate-600 text-sm mb-1">
            <Calendar className="w-4 h-4" />
            Created
          </div>
          <div className="text-lg font-semibold text-slate-900">
            {formatDate(manifest.created_at)}
          </div>
        </div>
        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <div className="flex items-center gap-2 text-slate-600 text-sm mb-1">
            <Database className="w-4 h-4" />
            Source
          </div>
          <span className={`inline-block px-2 py-1 rounded text-sm font-medium ${toolColors[manifest.created_by_tool]}`}>
            {manifest.created_by_tool.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Aggregation Levels */}
      {manifest.aggregation_levels && manifest.aggregation_levels.length > 0 && (
        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <h2 className="font-semibold text-slate-900 mb-2">Aggregation Levels</h2>
          <div className="flex gap-2">
            {manifest.aggregation_levels.map((level) => (
              <span key={level} className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                {level}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Schema */}
      <div className="bg-white rounded-lg border border-slate-200 p-4">
        <h2 className="font-semibold text-slate-900 mb-4">Schema</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200">
                <th className="text-left py-2 px-3 font-medium text-slate-600">Column</th>
                <th className="text-left py-2 px-3 font-medium text-slate-600">Type</th>
                <th className="text-left py-2 px-3 font-medium text-slate-600">Nullable</th>
                <th className="text-left py-2 px-3 font-medium text-slate-600">Description</th>
              </tr>
            </thead>
            <tbody>
              {manifest.columns.map((col) => (
                <tr key={col.name} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="py-2 px-3 font-mono text-slate-900">{col.name}</td>
                  <td className="py-2 px-3">
                    <span className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded text-xs">
                      {col.dtype}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-slate-600">{col.nullable ? 'Yes' : 'No'}</td>
                  <td className="py-2 px-3 text-slate-600">{col.description || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Data Preview */}
      <div className="bg-white rounded-lg border border-slate-200 p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-slate-900">Data Preview</h2>
          <button className="inline-flex items-center gap-1 text-sm text-primary-600 hover:text-primary-700">
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
        {previewLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-primary-600" />
          </div>
        ) : preview ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50">
                  {preview.columns.map((col) => (
                    <th key={col} className="text-left py-2 px-3 font-medium text-slate-600 whitespace-nowrap">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {preview.rows.map((row, idx) => (
                  <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50">
                    {preview.columns.map((col) => (
                      <td key={col} className="py-2 px-3 text-slate-900 whitespace-nowrap">
                        {String(row[col] ?? '')}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
            {preview.total_rows > preview.rows.length && (
              <p className="text-center text-sm text-slate-500 mt-4">
                Showing {preview.rows.length} of {preview.total_rows.toLocaleString()} rows
              </p>
            )}
          </div>
        ) : (
          <p className="text-center text-slate-500 py-8">No preview available</p>
        )}
      </div>

      {/* Lineage */}
      {lineage && (lineage.parents.length > 0 || lineage.children.length > 0) && (
        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <h2 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <GitBranch className="w-5 h-5" />
            Lineage
          </h2>
          <div className="grid md:grid-cols-2 gap-6">
            {lineage.parents.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-slate-600 mb-2">Parent Datasets</h3>
                <div className="space-y-2">
                  {lineage.parents.map((parent) => (
                    <Link
                      key={parent.dataset_id}
                      to={`/datasets/${parent.dataset_id}`}
                      className="block p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors"
                    >
                      <div className="font-medium text-slate-900">{parent.name}</div>
                      <div className="text-sm text-slate-500">{parent.row_count.toLocaleString()} rows</div>
                    </Link>
                  ))}
                </div>
              </div>
            )}
            {lineage.children.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-slate-600 mb-2">Derived Datasets</h3>
                <div className="space-y-2">
                  {lineage.children.map((child) => (
                    <Link
                      key={child.dataset_id}
                      to={`/datasets/${child.dataset_id}`}
                      className="block p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors"
                    >
                      <div className="font-medium text-slate-900">{child.name}</div>
                      <div className="text-sm text-slate-500">{child.row_count.toLocaleString()} rows</div>
                    </Link>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
