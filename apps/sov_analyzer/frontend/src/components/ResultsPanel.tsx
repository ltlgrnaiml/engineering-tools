import { useQuery } from '@tanstack/react-query'
import { 
  CheckCircle2, 
  XCircle, 
  Download, 
  Presentation, 
  RefreshCw,
  Loader2,
  TrendingUp,
  AlertTriangle
} from 'lucide-react'

interface ResultsPanelProps {
  analysisId: string
  onNewAnalysis: () => void
}

interface ANOVAResult {
  analysis_id: string
  status: 'completed' | 'failed' | 'running'
  dataset_name: string
  factors: string[]
  response_columns: string[]
  results: {
    response: string
    anova_table: {
      source: string
      df: number
      ss: number
      ms: number
      f_value: number
      p_value: number
      significant: boolean
      variance_contribution: number
    }[]
    total_variance: number
    r_squared: number
  }[]
  output_dataset_id?: string
  error?: string
}

async function fetchResults(id: string): Promise<ANOVAResult> {
  const response = await fetch(`/api/sov/v1/analysis/${id}`)
  if (!response.ok) throw new Error('Failed to fetch results')
  return response.json()
}

export function ResultsPanel({ analysisId, onNewAnalysis }: ResultsPanelProps) {
  const { data: results, isLoading, error } = useQuery({
    queryKey: ['sov-results', analysisId],
    queryFn: () => fetchResults(analysisId),
    refetchInterval: (query) => {
      if (query.state.data?.status === 'running') return 2000
      return false
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
      </div>
    )
  }

  if (error || !results) {
    return (
      <div className="text-center py-16">
        <XCircle className="w-12 h-12 mx-auto mb-4 text-red-500" />
        <h3 className="text-lg font-medium text-slate-900">Failed to Load Results</h3>
        <button
          onClick={onNewAnalysis}
          className="mt-4 px-4 py-2 bg-slate-100 hover:bg-slate-200 rounded-lg font-medium"
        >
          Start New Analysis
        </button>
      </div>
    )
  }

  if (results.status === 'running') {
    return (
      <div className="text-center py-16">
        <Loader2 className="w-12 h-12 mx-auto mb-4 text-purple-500 animate-spin" />
        <h3 className="text-lg font-medium text-slate-900">Analysis in Progress</h3>
        <p className="text-slate-600 mt-1">Computing variance components...</p>
      </div>
    )
  }

  if (results.status === 'failed') {
    return (
      <div className="text-center py-16">
        <XCircle className="w-12 h-12 mx-auto mb-4 text-red-500" />
        <h3 className="text-lg font-medium text-slate-900">Analysis Failed</h3>
        <p className="text-red-600 mt-1">{results.error || 'Unknown error occurred'}</p>
        <button
          onClick={onNewAnalysis}
          className="mt-4 px-4 py-2 bg-slate-100 hover:bg-slate-200 rounded-lg font-medium"
        >
          Try Again
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">ANOVA Results</h2>
          <p className="text-slate-600 mt-1">
            Analysis of: <span className="font-medium">{results.dataset_name}</span>
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={onNewAnalysis}
            className="px-4 py-2 bg-slate-100 hover:bg-slate-200 rounded-lg font-medium inline-flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            New Analysis
          </button>
          {results.output_dataset_id && (
            <a
              href={`/tools/pptx?dataset=${results.output_dataset_id}`}
              className="px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-lg font-medium inline-flex items-center gap-2"
            >
              <Presentation className="w-4 h-4" />
              Generate Report
            </a>
          )}
        </div>
      </div>

      {/* Results for each response variable */}
      {results.results.map((result) => (
        <div key={result.response} className="bg-white rounded-lg border border-slate-200 overflow-hidden">
          <div className="px-4 py-3 bg-slate-50 border-b border-slate-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-purple-600" />
                <h3 className="font-medium text-slate-900">Response: {result.response}</h3>
              </div>
              <div className="text-sm text-slate-600">
                R² = {(result.r_squared * 100).toFixed(1)}%
              </div>
            </div>
          </div>

          {/* ANOVA Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="text-left px-4 py-2 font-medium text-slate-600">Source</th>
                  <th className="text-right px-4 py-2 font-medium text-slate-600">DF</th>
                  <th className="text-right px-4 py-2 font-medium text-slate-600">Sum Sq</th>
                  <th className="text-right px-4 py-2 font-medium text-slate-600">Mean Sq</th>
                  <th className="text-right px-4 py-2 font-medium text-slate-600">F</th>
                  <th className="text-right px-4 py-2 font-medium text-slate-600">P-value</th>
                  <th className="text-right px-4 py-2 font-medium text-slate-600">% Var</th>
                  <th className="text-center px-4 py-2 font-medium text-slate-600">Sig</th>
                </tr>
              </thead>
              <tbody>
                {result.anova_table.map((row) => (
                  <tr key={row.source} className="border-t border-slate-100">
                    <td className="px-4 py-2 font-medium text-slate-900">{row.source}</td>
                    <td className="px-4 py-2 text-right text-slate-600">{row.df}</td>
                    <td className="px-4 py-2 text-right text-slate-600">{row.ss.toFixed(4)}</td>
                    <td className="px-4 py-2 text-right text-slate-600">{row.ms.toFixed(4)}</td>
                    <td className="px-4 py-2 text-right text-slate-600">{row.f_value.toFixed(2)}</td>
                    <td className={`px-4 py-2 text-right ${row.p_value < 0.05 ? 'text-purple-600 font-medium' : 'text-slate-600'}`}>
                      {row.p_value < 0.001 ? '<0.001' : row.p_value.toFixed(4)}
                    </td>
                    <td className="px-4 py-2 text-right text-slate-600">
                      {(row.variance_contribution * 100).toFixed(1)}%
                    </td>
                    <td className="px-4 py-2 text-center">
                      {row.significant ? (
                        <CheckCircle2 className="w-5 h-5 text-green-500 inline" />
                      ) : (
                        <span className="text-slate-400">-</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Variance Contribution Chart (simplified bar) */}
          <div className="px-4 py-3 border-t border-slate-200">
            <h4 className="text-sm font-medium text-slate-700 mb-2">Variance Contribution</h4>
            <div className="space-y-2">
              {result.anova_table
                .filter(row => row.source !== 'Residual')
                .sort((a, b) => b.variance_contribution - a.variance_contribution)
                .map((row) => (
                  <div key={row.source} className="flex items-center gap-3">
                    <div className="w-24 text-sm text-slate-600 truncate">{row.source}</div>
                    <div className="flex-1 h-4 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${row.significant ? 'bg-purple-500' : 'bg-slate-300'}`}
                        style={{ width: `${row.variance_contribution * 100}%` }}
                      />
                    </div>
                    <div className="w-16 text-sm text-right text-slate-600">
                      {(row.variance_contribution * 100).toFixed(1)}%
                    </div>
                  </div>
                ))}
            </div>
          </div>

          {/* Significant factors summary */}
          {result.anova_table.some(r => r.significant) && (
            <div className="px-4 py-3 bg-green-50 border-t border-green-200">
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-5 h-5 text-green-600 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-green-900">Significant Sources of Variation</p>
                  <p className="text-sm text-green-800 mt-1">
                    {result.anova_table
                      .filter(r => r.significant && r.source !== 'Residual')
                      .map(r => r.source)
                      .join(', ')} explain {
                        (result.anova_table
                          .filter(r => r.significant && r.source !== 'Residual')
                          .reduce((sum, r) => sum + r.variance_contribution, 0) * 100
                        ).toFixed(1)
                      }% of the variance.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      ))}

      {/* Export Actions */}
      {results.output_dataset_id && (
        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <h3 className="font-medium text-slate-900 mb-3">Export Results</h3>
          <div className="flex gap-3">
            <a
              href={`/datasets/${results.output_dataset_id}`}
              className="px-4 py-2 bg-slate-100 hover:bg-slate-200 rounded-lg font-medium inline-flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              View Result DataSet
            </a>
            <a
              href={`/tools/pptx?dataset=${results.output_dataset_id}`}
              className="px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-lg font-medium inline-flex items-center gap-2"
            >
              <Presentation className="w-4 h-4" />
              Generate PowerPoint Report
            </a>
          </div>
        </div>
      )}
    </div>
  )
}
