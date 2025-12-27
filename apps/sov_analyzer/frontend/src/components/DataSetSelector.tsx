import { useQuery } from '@tanstack/react-query'
import { Database, Calendar, FileText, Loader2 } from 'lucide-react'

interface DataSetRef {
  dataset_id: string
  name: string
  created_by_tool: string
  row_count: number
  created_at: string
}

interface DataSetSelectorProps {
  onSelect: (datasetId: string) => void
}

async function fetchDatasets(): Promise<DataSetRef[]> {
  const response = await fetch('/api/datasets/v1/')
  if (!response.ok) throw new Error('Failed to fetch datasets')
  return response.json()
}

export function DataSetSelector({ onSelect }: DataSetSelectorProps) {
  const { data: datasets, isLoading, error } = useQuery({
    queryKey: ['datasets'],
    queryFn: fetchDatasets,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-16">
        <p className="text-red-600">Failed to load datasets</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Select Input DataSet</h2>
        <p className="text-slate-600 mt-1">Choose a dataset to analyze for sources of variation.</p>
      </div>

      {datasets && datasets.length > 0 ? (
        <div className="grid gap-4">
          {datasets.map((dataset) => (
            <button
              key={dataset.dataset_id}
              onClick={() => onSelect(dataset.dataset_id)}
              className="flex items-center justify-between p-4 bg-white rounded-lg border border-slate-200 hover:border-purple-300 hover:shadow-md transition-all text-left"
            >
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-purple-100 flex items-center justify-center">
                  <Database className="w-6 h-6 text-purple-600" />
                </div>
                <div>
                  <div className="font-medium text-slate-900">{dataset.name}</div>
                  <div className="flex items-center gap-3 text-sm text-slate-500 mt-1">
                    <span className="uppercase text-xs bg-slate-100 px-2 py-0.5 rounded">
                      {dataset.created_by_tool}
                    </span>
                    <span className="flex items-center gap-1">
                      <FileText className="w-3 h-3" />
                      {dataset.row_count.toLocaleString()} rows
                    </span>
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {new Date(dataset.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </div>
              <div className="text-purple-600 font-medium text-sm">
                Select →
              </div>
            </button>
          ))}
        </div>
      ) : (
        <div className="text-center py-16 bg-white rounded-lg border border-slate-200">
          <Database className="w-12 h-12 mx-auto mb-4 text-slate-300" />
          <h3 className="text-lg font-medium text-slate-900">No DataSets Available</h3>
          <p className="text-slate-600 mt-1">
            Export data from the Data Aggregator to create a dataset for analysis.
          </p>
        </div>
      )}
    </div>
  )
}
