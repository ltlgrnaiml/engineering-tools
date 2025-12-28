import { useState } from 'react'
import { FileSpreadsheet, ChevronRight, Loader2, ArrowLeft } from 'lucide-react'
import { SelectionPanel } from './components/stages/SelectionPanel'
import { ContextPanel } from './components/stages/ContextPanel'
import { TableAvailabilityPanel } from './components/stages/TableAvailabilityPanel'
import { TableSelectionPanel } from './components/stages/TableSelectionPanel'
import { PreviewPanel } from './components/stages/PreviewPanel'
import { ParsePanel } from './components/stages/ParsePanel'
import { ExportPanel } from './components/stages/ExportPanel'
import { useRun, useStageAction } from './hooks/useRun'
import { DebugProvider, DebugPanel } from './components/debug'

type Stage = 'selection' | 'context' | 'table_availability' | 'table_selection' | 'preview' | 'parse' | 'export'

const stages: { id: Stage; label: string; optional?: boolean }[] = [
  { id: 'selection', label: 'File Selection' },
  { id: 'context', label: 'Context', optional: true },
  { id: 'table_availability', label: 'Table Availability' },
  { id: 'table_selection', label: 'Table Selection' },
  { id: 'preview', label: 'Preview', optional: true },
  { id: 'parse', label: 'Parse' },
  { id: 'export', label: 'Export' },
]

function App() {
  const [runId, setRunId] = useState<string | null>(null)
  const { run, isLoading, createRun } = useRun(runId)
  const { unlockStage } = useStageAction(runId || '')

  const handleCreateRun = async () => {
    const newRun = await createRun()
    setRunId(newRun.run_id)
  }

  const currentStage = run?.current_stage || 'selection'
  const stageIndex = stages.findIndex(s => s.id === currentStage)

  // Handle navigating back to a previous stage (per ADR-0001: backward cascade)
  const handleNavigateToStage = async (targetStageId: Stage) => {
    const targetIndex = stages.findIndex(s => s.id === targetStageId)
    if (targetIndex < stageIndex && runId) {
      // Unlock the target stage (cascades downstream per ADR-0001-DAT)
      try {
        await unlockStage.mutateAsync(targetStageId)
      } catch (error) {
        console.error('Failed to navigate back:', error)
      }
    }
  }

  // Handle going back one step
  const handleBack = () => {
    if (stageIndex > 0) {
      const prevStage = stages[stageIndex - 1]
      handleNavigateToStage(prevStage.id)
    }
  }

  return (
    <DebugProvider>
    <div className="min-h-screen">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-500 flex items-center justify-center">
            <FileSpreadsheet className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-slate-900">Data Aggregator</h1>
            <p className="text-sm text-slate-500">Parse, transform, and aggregate data</p>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Stage Sidebar */}
        <aside className="w-64 bg-white border-r border-slate-200 min-h-[calc(100vh-73px)]">
          <nav className="p-4 space-y-1">
            {stages.map((stage, idx) => {
              const isActive = stage.id === currentStage
              const isCompleted = idx < stageIndex
              const isLocked = idx > stageIndex
              const canNavigate = isCompleted && runId

              return (
                <button
                  key={stage.id}
                  onClick={() => canNavigate && handleNavigateToStage(stage.id)}
                  disabled={!canNavigate && !isActive}
                  className={`
                    w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-left
                    ${isActive ? 'bg-emerald-50 text-emerald-700 font-medium' : ''}
                    ${isCompleted ? 'text-slate-700 hover:bg-slate-50 cursor-pointer' : ''}
                    ${isLocked ? 'text-slate-400 cursor-not-allowed' : ''}
                    ${canNavigate ? 'hover:bg-emerald-50' : ''}
                    transition-colors
                  `}
                  title={canNavigate ? `Go back to ${stage.label}` : undefined}
                >
                  <div className={`
                    w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium
                    ${isActive ? 'bg-emerald-500 text-white' : ''}
                    ${isCompleted ? 'bg-emerald-100 text-emerald-700' : ''}
                    ${isLocked ? 'bg-slate-100 text-slate-400' : ''}
                  `}>
                    {isCompleted ? '✓' : idx + 1}
                  </div>
                  <span className="flex-1">{stage.label}</span>
                  {stage.optional && (
                    <span className="text-xs text-slate-400">(optional)</span>
                  )}
                  {isActive && <ChevronRight className="w-4 h-4" />}
                </button>
              )
            })}
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-6">
          {!runId ? (
            <div className="text-center py-16">
              <FileSpreadsheet className="w-16 h-16 mx-auto mb-4 text-slate-300" />
              <h2 className="text-xl font-semibold text-slate-900 mb-2">Start a New Aggregation Run</h2>
              <p className="text-slate-600 mb-6">
                Select files, configure extraction, and export aggregated data.
              </p>
              <button
                onClick={handleCreateRun}
                className="px-6 py-3 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg font-medium transition-colors"
              >
                Create New Run
              </button>
            </div>
          ) : isLoading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
            </div>
          ) : (
            <div className="max-w-4xl">
              {/* Back Button - shown for all stages except first */}
              {stageIndex > 0 && (
                <button
                  onClick={handleBack}
                  className="flex items-center gap-2 text-slate-600 hover:text-slate-900 mb-4 transition-colors"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span>Back to {stages[stageIndex - 1]?.label}</span>
                </button>
              )}
              
              {currentStage === 'selection' && <SelectionPanel runId={runId} />}
              {currentStage === 'context' && <ContextPanel runId={runId} />}
              {currentStage === 'table_availability' && <TableAvailabilityPanel runId={runId} />}
              {currentStage === 'table_selection' && <TableSelectionPanel runId={runId} />}
              {currentStage === 'preview' && <PreviewPanel runId={runId} />}
              {currentStage === 'parse' && <ParsePanel runId={runId} />}
              {currentStage === 'export' && <ExportPanel runId={runId} />}
            </div>
          )}
        </main>
      </div>
      <DebugPanel />
    </div>
    </DebugProvider>
  )
}

export default App
