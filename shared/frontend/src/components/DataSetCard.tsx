import { Database, FileText, Calendar, GitBranch, ArrowRight } from 'lucide-react'

interface DataSetCardProps {
  datasetId: string
  name: string
  sourceTool: 'dat' | 'sov' | 'pptx' | 'manual'
  rowCount: number
  columnCount: number
  createdAt: string
  parentCount?: number
  sizeBytes?: number
  onClick?: () => void
  onPipeTo?: (tool: 'pptx' | 'sov') => void
  className?: string
}

const toolColors = {
  dat: 'bg-emerald-100 text-emerald-700',
  sov: 'bg-purple-100 text-purple-700',
  pptx: 'bg-orange-100 text-orange-700',
  manual: 'bg-slate-100 text-slate-600',
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins} min ago`
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
  if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`

  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
  })
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

export function DataSetCard({
  datasetId,
  name,
  sourceTool,
  rowCount,
  columnCount,
  createdAt,
  parentCount = 0,
  sizeBytes,
  onClick,
  onPipeTo,
  className = '',
}: DataSetCardProps) {
  return (
    <div
      className={`
        bg-white border border-slate-200 rounded-lg p-4
        hover:border-slate-300 hover:shadow-sm transition-all
        ${onClick ? 'cursor-pointer' : ''}
        ${className}
      `}
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3 min-w-0">
          <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center flex-shrink-0">
            <Database className="w-5 h-5 text-slate-500" />
          </div>
          <div className="min-w-0">
            <h3 className="font-medium text-slate-900 truncate">{name}</h3>
            <p className="text-xs text-slate-500 font-mono truncate">{datasetId}</p>
          </div>
        </div>
        <span className={`px-2 py-1 text-xs font-medium rounded-full uppercase flex-shrink-0 ${toolColors[sourceTool]}`}>
          {sourceTool}
        </span>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-slate-500">
        <span className="flex items-center gap-1">
          <FileText className="w-3.5 h-3.5" />
          {rowCount.toLocaleString()} rows × {columnCount} cols
        </span>
        {sizeBytes && sizeBytes > 0 && (
          <span>{formatBytes(sizeBytes)}</span>
        )}
        <span className="flex items-center gap-1">
          <Calendar className="w-3.5 h-3.5" />
          {formatDate(createdAt)}
        </span>
        {parentCount > 0 && (
          <span className="flex items-center gap-1">
            <GitBranch className="w-3.5 h-3.5" />
            {parentCount} parent{parentCount > 1 ? 's' : ''}
          </span>
        )}
      </div>

      {onPipeTo && (
        <div className="mt-4 pt-3 border-t border-slate-100 flex gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation()
              onPipeTo('pptx')
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-orange-600 bg-orange-50 hover:bg-orange-100 rounded-md transition-colors"
          >
            <ArrowRight className="w-3 h-3" />
            Pipe to PPTX
          </button>
          {sourceTool === 'dat' && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                onPipeTo('sov')
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-purple-600 bg-purple-50 hover:bg-purple-100 rounded-md transition-colors"
            >
              <ArrowRight className="w-3 h-3" />
              Pipe to SOV
            </button>
          )}
        </div>
      )}
    </div>
  )
}
