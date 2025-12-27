import { useState, useEffect } from 'react'
import { Table, RefreshCw, ChevronLeft, ChevronRight } from 'lucide-react'
import { api } from '../lib/api'

interface DataPreviewPanelProps {
  projectId: string
  columns?: string[]
  maxRows?: number
}

export function DataPreviewPanel({
  projectId,
  columns,
  maxRows = 10,
}: DataPreviewPanelProps) {
  const [data, setData] = useState<{
    rows: Array<Record<string, any>>
    total_rows: number
    total_columns: number
    columns: string[]
  } | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [visibleColumns, setVisibleColumns] = useState<string[]>([])
  const [columnOffset, setColumnOffset] = useState(0)
  const maxVisibleColumns = 6

  const fetchPreview = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await api.getDataPreview(projectId, maxRows, columns)
      setData(result)
      setVisibleColumns(result.columns.slice(0, maxVisibleColumns))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load preview')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPreview()
  }, [projectId, columns?.join(','), maxRows])

  useEffect(() => {
    if (data) {
      setVisibleColumns(data.columns.slice(columnOffset, columnOffset + maxVisibleColumns))
    }
  }, [columnOffset, data])

  const canScrollLeft = columnOffset > 0
  const canScrollRight = data && columnOffset + maxVisibleColumns < data.columns.length

  if (loading) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-center gap-2 text-gray-500">
          <RefreshCw className="h-5 w-5 animate-spin" />
          <span>Loading preview...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="text-red-600 text-center">{error}</div>
        <button
          onClick={fetchPreview}
          className="mt-2 mx-auto block px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Retry
        </button>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6 text-center text-gray-500">
        No data available
      </div>
    )
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Table className="h-5 w-5 text-gray-600" />
          <span className="font-medium text-gray-900">Data Preview</span>
          <span className="text-sm text-gray-500">
            ({data.total_rows.toLocaleString()} rows, {data.total_columns} columns)
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setColumnOffset(Math.max(0, columnOffset - maxVisibleColumns))}
            disabled={!canScrollLeft}
            className="p-1 rounded hover:bg-gray-200 disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="h-5 w-5" />
          </button>
          <span className="text-sm text-gray-500">
            Columns {columnOffset + 1}-{Math.min(columnOffset + maxVisibleColumns, data.columns.length)} of {data.columns.length}
          </span>
          <button
            onClick={() => setColumnOffset(Math.min(data.columns.length - maxVisibleColumns, columnOffset + maxVisibleColumns))}
            disabled={!canScrollRight}
            className="p-1 rounded hover:bg-gray-200 disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <ChevronRight className="h-5 w-5" />
          </button>
          <button
            onClick={fetchPreview}
            className="p-1 rounded hover:bg-gray-200"
            title="Refresh"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r">
                #
              </th>
              {visibleColumns.map((col) => (
                <th
                  key={col}
                  className="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase tracking-wider border-r truncate max-w-[150px]"
                  title={col}
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {data.rows.map((row, idx) => (
              <tr key={idx} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                <td className="px-3 py-2 text-gray-400 border-r">{idx + 1}</td>
                {visibleColumns.map((col) => (
                  <td
                    key={col}
                    className="px-3 py-2 text-gray-900 border-r truncate max-w-[150px]"
                    title={String(row[col] ?? '')}
                  >
                    {row[col] !== null && row[col] !== undefined ? String(row[col]) : <span className="text-gray-400 italic">null</span>}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {data.rows.length < data.total_rows && (
        <div className="px-4 py-2 bg-gray-50 border-t text-center text-sm text-gray-500">
          Showing {data.rows.length} of {data.total_rows.toLocaleString()} rows
        </div>
      )}
    </div>
  )
}
