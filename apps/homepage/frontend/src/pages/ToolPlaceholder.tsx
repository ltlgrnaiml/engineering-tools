import { ExternalLink, FileCode, Wrench } from 'lucide-react'

interface ToolPlaceholderProps {
  tool: 'dat' | 'pptx' | 'sov'
}

const toolInfo = {
  dat: {
    name: 'Data Aggregator',
    description: 'Extract and aggregate data from multiple file formats (CSV, Excel, Parquet)',
    apiPath: '/api/dat',
    features: [
      'Multi-format file parsing',
      'FSM-based stage orchestration',
      'DataSet export with lineage tracking',
      'Progress tracking and cancellation support',
    ],
  },
  pptx: {
    name: 'PowerPoint Generator',
    description: 'Generate PowerPoint presentations from templates and data',
    apiPath: '/api/pptx',
    features: [
      'Template-based generation',
      'DataSet integration',
      'Dynamic content rendering',
      'Preview and validation',
    ],
  },
  sov: {
    name: 'SOV Analyzer',
    description: 'Source of Variation analysis using ANOVA',
    apiPath: '/api/sov',
    features: [
      'One-way and n-way ANOVA',
      'Variance component estimation',
      'Statistical significance testing',
      'Results export as DataSet',
    ],
  },
}

export function ToolPlaceholder({ tool }: ToolPlaceholderProps) {
  const info = toolInfo[tool]

  return (
    <div className="max-w-4xl mx-auto py-12 px-4">
      <div className="bg-white rounded-lg shadow-lg p-8">
        <div className="flex items-center gap-3 mb-6">
          <Wrench className="w-8 h-8 text-primary-600" />
          <h1 className="text-3xl font-bold text-slate-900">{info.name}</h1>
        </div>

        <p className="text-lg text-slate-600 mb-8">{info.description}</p>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
          <h2 className="text-lg font-semibold text-blue-900 mb-2">
            🚧 Frontend UI Coming Soon
          </h2>
          <p className="text-blue-800">
            The web interface for this tool is under development. You can currently access the tool
            via its REST API.
          </p>
        </div>

        <div className="mb-8">
          <h2 className="text-xl font-semibold text-slate-900 mb-4">Features</h2>
          <ul className="space-y-2">
            {info.features.map((feature, index) => (
              <li key={index} className="flex items-start gap-2">
                <span className="text-primary-600 mt-1">✓</span>
                <span className="text-slate-700">{feature}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="flex flex-col sm:flex-row gap-4">
          <a
            href={`http://localhost:8000${info.apiPath}/docs`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            <FileCode className="w-5 h-5" />
            <span>View API Documentation</span>
            <ExternalLink className="w-4 h-4" />
          </a>

          <a
            href={`http://localhost:8000${info.apiPath}/health`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors"
          >
            <span>Health Check</span>
            <ExternalLink className="w-4 h-4" />
          </a>
        </div>

        <div className="mt-8 pt-8 border-t border-slate-200">
          <h3 className="text-sm font-semibold text-slate-900 mb-2">Quick Start</h3>
          <div className="bg-slate-50 rounded-lg p-4 font-mono text-sm text-slate-800">
            <div className="mb-2"># Test the API endpoint</div>
            <div>curl http://localhost:8000{info.apiPath}/health</div>
          </div>
        </div>
      </div>
    </div>
  )
}
