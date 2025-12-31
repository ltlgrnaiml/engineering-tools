import { useState } from 'react'
import { BarChart3, Home } from 'lucide-react'
import { DataSetSelector } from './components/DataSetSelector'
import { AnalysisConfig } from './components/AnalysisConfig'
import { ResultsPanel } from './components/ResultsPanel'

type Step = 'select' | 'configure' | 'results'

export default function App() {
  const [step, setStep] = useState<Step>('select')
  const [selectedDatasetId, setSelectedDatasetId] = useState<string | null>(null)
  const [analysisId, setAnalysisId] = useState<string | null>(null)

  const handleDatasetSelect = (datasetId: string) => {
    setSelectedDatasetId(datasetId)
    setStep('configure')
  }

  const handleAnalysisComplete = (id: string) => {
    setAnalysisId(id)
    setStep('results')
  }

  const handleReset = () => {
    setStep('select')
    setSelectedDatasetId(null)
    setAnalysisId(null)
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-purple-500 flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-slate-900">SOV Analyzer</h1>
              <p className="text-sm text-slate-500">Source of Variation Analysis</p>
            </div>
          </div>
          <a
            href="http://localhost:5174"
            target="_top"
            className="flex items-center gap-2 px-3 py-2 text-sm text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-md transition-colors"
          >
            <Home className="w-4 h-4" />
            <span>Engineering Tools</span>
          </a>
        </div>
      </header>

      {/* Progress Steps */}
      <div className="bg-white border-b border-slate-200 px-6 py-3">
        <div className="flex items-center gap-4">
          {[
            { id: 'select', label: '1. Select DataSet' },
            { id: 'configure', label: '2. Configure Analysis' },
            { id: 'results', label: '3. View Results' },
          ].map((s, idx) => (
            <div key={s.id} className="flex items-center gap-2">
              <div className={`
                w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium
                ${step === s.id ? 'bg-purple-500 text-white' : 
                  idx < ['select', 'configure', 'results'].indexOf(step) 
                    ? 'bg-purple-100 text-purple-700' 
                    : 'bg-slate-100 text-slate-500'
                }
              `}>
                {idx + 1}
              </div>
              <span className={`text-sm ${step === s.id ? 'font-medium text-slate-900' : 'text-slate-500'}`}>
                {s.label}
              </span>
              {idx < 2 && <div className="w-8 h-px bg-slate-300" />}
            </div>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto p-6">
        {step === 'select' && (
          <DataSetSelector onSelect={handleDatasetSelect} />
        )}
        {step === 'configure' && selectedDatasetId && (
          <AnalysisConfig 
            datasetId={selectedDatasetId} 
            onComplete={handleAnalysisComplete}
            onBack={() => setStep('select')}
          />
        )}
        {step === 'results' && analysisId && (
          <ResultsPanel 
            analysisId={analysisId} 
            onNewAnalysis={handleReset}
          />
        )}
      </main>
    </div>
  )
}
