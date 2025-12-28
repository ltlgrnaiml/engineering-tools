import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { ArrowLeft, Settings, Play, Loader2, Info } from 'lucide-react'

interface AnalysisConfigProps {
  datasetId: string
  onComplete: (analysisId: string) => void
  onBack: () => void
}

interface DataSetManifest {
  dataset_id: string
  name: string
  columns: { name: string; dtype: string }[]
  row_count: number
}

interface ANOVAConfig {
  factors: string[]
  response_columns: string[]
  alpha: number
  include_interactions: boolean
}

async function fetchDatasetManifest(id: string): Promise<DataSetManifest> {
  const response = await fetch(`/api/v1/datasets/${id}`)
  if (!response.ok) throw new Error('Failed to fetch dataset')
  return response.json()
}

async function runAnalysis(datasetId: string, config: ANOVAConfig): Promise<{ analysis_id: string }> {
  const response = await fetch('/api/sov/v1/analyses', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dataset_id: datasetId, config }),
  })
  if (!response.ok) throw new Error('Failed to start analysis')
  return response.json()
}

export function AnalysisConfig({ datasetId, onComplete, onBack }: AnalysisConfigProps) {
  const [selectedFactors, setSelectedFactors] = useState<string[]>([])
  const [selectedResponses, setSelectedResponses] = useState<string[]>([])
  const [alpha, setAlpha] = useState(0.05)
  const [includeInteractions, setIncludeInteractions] = useState(false)

  const { data: manifest, isLoading } = useQuery({
    queryKey: ['dataset-manifest', datasetId],
    queryFn: () => fetchDatasetManifest(datasetId),
  })

  const analysisMutation = useMutation({
    mutationFn: () => runAnalysis(datasetId, {
      factors: selectedFactors,
      response_columns: selectedResponses,
      alpha,
      include_interactions: includeInteractions,
    }),
    onSuccess: (data) => {
      onComplete(data.analysis_id)
    },
  })

  const toggleFactor = (col: string) => {
    setSelectedFactors(prev =>
      prev.includes(col) ? prev.filter(c => c !== col) : [...prev, col]
    )
    // Remove from responses if added to factors
    setSelectedResponses(prev => prev.filter(c => c !== col))
  }

  const toggleResponse = (col: string) => {
    setSelectedResponses(prev =>
      prev.includes(col) ? prev.filter(c => c !== col) : [...prev, col]
    )
    // Remove from factors if added to responses
    setSelectedFactors(prev => prev.filter(c => c !== col))
  }

  const numericColumns = manifest?.columns.filter(c => 
    ['float', 'int', 'Float64', 'Int64', 'Float32', 'Int32'].some(t => c.dtype.includes(t))
  ) || []

  const categoricalColumns = manifest?.columns.filter(c => 
    ['str', 'Utf8', 'Categorical', 'object'].some(t => c.dtype.includes(t))
  ) || []

  const canRun = selectedFactors.length > 0 && selectedResponses.length > 0

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <button
          onClick={onBack}
          className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5 text-slate-600" />
        </button>
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Configure ANOVA Analysis</h2>
          <p className="text-slate-600 mt-1">
            Analyzing: <span className="font-medium">{manifest?.name}</span> ({manifest?.row_count.toLocaleString()} rows)
          </p>
        </div>
      </div>

      {/* Factor Selection */}
      <div className="bg-white rounded-lg border border-slate-200 p-4">
        <div className="flex items-center gap-2 mb-3">
          <Settings className="w-5 h-5 text-slate-600" />
          <h3 className="font-medium text-slate-900">Factor Variables (Categorical)</h3>
        </div>
        <p className="text-sm text-slate-600 mb-3">
          Select the categorical variables that may influence your response.
        </p>
        <div className="flex flex-wrap gap-2">
          {categoricalColumns.map(col => (
            <button
              key={col.name}
              onClick={() => toggleFactor(col.name)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                selectedFactors.includes(col.name)
                  ? 'bg-purple-500 text-white'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              {col.name}
            </button>
          ))}
          {categoricalColumns.length === 0 && (
            <p className="text-sm text-slate-500 italic">No categorical columns detected</p>
          )}
        </div>
      </div>

      {/* Response Selection */}
      <div className="bg-white rounded-lg border border-slate-200 p-4">
        <div className="flex items-center gap-2 mb-3">
          <Settings className="w-5 h-5 text-slate-600" />
          <h3 className="font-medium text-slate-900">Response Variables (Numeric)</h3>
        </div>
        <p className="text-sm text-slate-600 mb-3">
          Select the numeric variables to analyze for sources of variation.
        </p>
        <div className="flex flex-wrap gap-2">
          {numericColumns.map(col => (
            <button
              key={col.name}
              onClick={() => toggleResponse(col.name)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                selectedResponses.includes(col.name)
                  ? 'bg-purple-500 text-white'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              {col.name}
            </button>
          ))}
          {numericColumns.length === 0 && (
            <p className="text-sm text-slate-500 italic">No numeric columns detected</p>
          )}
        </div>
      </div>

      {/* Advanced Options */}
      <div className="bg-white rounded-lg border border-slate-200 p-4">
        <h3 className="font-medium text-slate-900 mb-3">Advanced Options</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <label className="font-medium text-slate-700">Significance Level (α)</label>
              <p className="text-sm text-slate-500">P-value threshold for significance</p>
            </div>
            <select
              value={alpha}
              onChange={(e) => setAlpha(parseFloat(e.target.value))}
              className="px-3 py-2 border border-slate-300 rounded-lg"
            >
              <option value={0.01}>0.01</option>
              <option value={0.05}>0.05</option>
              <option value={0.10}>0.10</option>
            </select>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <label className="font-medium text-slate-700">Include Interactions</label>
              <p className="text-sm text-slate-500">Analyze factor interactions (slower)</p>
            </div>
            <button
              onClick={() => setIncludeInteractions(!includeInteractions)}
              className={`w-12 h-6 rounded-full transition-colors ${
                includeInteractions ? 'bg-purple-500' : 'bg-slate-300'
              }`}
            >
              <div className={`w-5 h-5 rounded-full bg-white shadow transition-transform ${
                includeInteractions ? 'translate-x-6' : 'translate-x-0.5'
              }`} />
            </button>
          </div>
        </div>
      </div>

      {/* Summary & Run */}
      <div className="bg-purple-50 rounded-lg border border-purple-200 p-4">
        <div className="flex items-start gap-3">
          <Info className="w-5 h-5 text-purple-600 mt-0.5" />
          <div className="flex-1">
            <h3 className="font-medium text-purple-900">Analysis Summary</h3>
            <ul className="mt-2 text-sm text-purple-800 space-y-1">
              <li>• Factors: {selectedFactors.length > 0 ? selectedFactors.join(', ') : 'None selected'}</li>
              <li>• Responses: {selectedResponses.length > 0 ? selectedResponses.join(', ') : 'None selected'}</li>
              <li>• Significance: α = {alpha}</li>
              <li>• Interactions: {includeInteractions ? 'Yes' : 'No'}</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-3">
        <button
          onClick={onBack}
          className="px-4 py-2 text-slate-700 hover:bg-slate-100 rounded-lg font-medium transition-colors"
        >
          Back
        </button>
        <button
          onClick={() => analysisMutation.mutate()}
          disabled={!canRun || analysisMutation.isPending}
          className="px-6 py-2 bg-purple-500 hover:bg-purple-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50 inline-flex items-center gap-2"
        >
          {analysisMutation.isPending ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Play className="w-5 h-5" />
          )}
          Run Analysis
        </button>
      </div>
    </div>
  )
}
