import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Database, ChevronDown, Check } from 'lucide-react'

interface DataSetManifest {
  id: string
  name: string
  description: string
  source_tool: string
  row_count: number
  created_at: string
}

interface DataSetPickerProps {
  value?: string
  onChange: (datasetId: string | undefined) => void
  placeholder?: string
  disabled?: boolean
  className?: string
}

async function fetchDatasets(): Promise<DataSetManifest[]> {
  const response = await fetch('/api/datasets')
  if (!response.ok) throw new Error('Failed to fetch datasets')
  return response.json()
}

export function DataSetPicker({
  value,
  onChange,
  placeholder = 'Select a DataSet...',
  disabled = false,
  className = '',
}: DataSetPickerProps) {
  const [isOpen, setIsOpen] = useState(false)

  const { data: datasets, isLoading } = useQuery({
    queryKey: ['datasets'],
    queryFn: fetchDatasets,
  })

  const selectedDataset = datasets?.find((d) => d.id === value)

  return (
    <div className={`relative ${className}`}>
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={`
          w-full flex items-center justify-between gap-2 px-3 py-2
          bg-white border border-slate-300 rounded-lg text-left
          hover:border-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500
          disabled:bg-slate-50 disabled:cursor-not-allowed
        `}
      >
        <div className="flex items-center gap-2 min-w-0">
          <Database className="w-4 h-4 text-slate-400 flex-shrink-0" />
          {isLoading ? (
            <span className="text-slate-400">Loading...</span>
          ) : selectedDataset ? (
            <div className="truncate">
              <span className="font-medium">{selectedDataset.name}</span>
              <span className="text-slate-500 text-sm ml-2">
                ({selectedDataset.row_count.toLocaleString()} rows)
              </span>
            </div>
          ) : (
            <span className="text-slate-400">{placeholder}</span>
          )}
        </div>
        <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && !disabled && (
        <div className="absolute z-10 mt-1 w-full bg-white border border-slate-200 rounded-lg shadow-lg max-h-60 overflow-auto">
          {datasets?.length === 0 ? (
            <div className="px-3 py-2 text-sm text-slate-500">No datasets available</div>
          ) : (
            datasets?.map((dataset) => (
              <button
                key={dataset.id}
                type="button"
                onClick={() => {
                  onChange(dataset.id)
                  setIsOpen(false)
                }}
                className={`
                  w-full flex items-center justify-between px-3 py-2 text-left
                  hover:bg-slate-50 transition-colors
                  ${dataset.id === value ? 'bg-primary-50' : ''}
                `}
              >
                <div>
                  <div className="font-medium text-slate-900">{dataset.name}</div>
                  <div className="text-xs text-slate-500">
                    {dataset.source_tool} • {dataset.row_count.toLocaleString()} rows
                  </div>
                </div>
                {dataset.id === value && <Check className="w-4 h-4 text-primary-600" />}
              </button>
            ))
          )}
        </div>
      )}
    </div>
  )
}
