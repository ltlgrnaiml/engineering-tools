import { useState, useMemo } from 'react'
import { FileSpreadsheet, Loader2 } from 'lucide-react'
import { SelectionPanel } from './components/stages/SelectionPanel'
import { ContextPanel } from './components/stages/ContextPanel'
import { TableAvailabilityPanel } from './components/stages/TableAvailabilityPanel'
import { TableSelectionPanel } from './components/stages/TableSelectionPanel'
import { PreviewPanel } from './components/stages/PreviewPanel'
import { ParsePanel } from './components/stages/ParsePanel'
import { ExportPanel } from './components/stages/ExportPanel'
import { useRun, useStageAction } from './hooks/useRun'
import { DebugProvider, DebugPanel } from './components/debug'
import { DATWizard, StageConfig, StageState } from './components/wizard'

type Stage = 'selection' | 'context' | 'table_availability' | 'table_selection' | 'preview' | 'parse' | 'export'

/**
 * DAT stage configuration for the horizontal wizard.
 * Per ADR-0041: Horizontal wizard stepper pattern.
 */
const STAGES: StageConfig[] = [
  {
    id: 'selection',
    label: 'Selection',
    description: 'Select files or folder containing data to aggregate',
  },
  {
    id: 'context',
    label: 'Context',
    description: 'Provide additional context for extraction',
    optional: true,
  },
  {
    id: 'table_availability',
    label: 'Tables',
    description: 'View available tables in selected files',
  },
  {
    id: 'table_selection',
    label: 'Table Select',
    description: 'Choose which tables to extract',
  },
  {
    id: 'preview',
    label: 'Preview',
    description: 'Preview extracted data before parsing',
    optional: true,
  },
  {
    id: 'parse',
    label: 'Parse',
    description: 'Parse and transform the data',
  },
  {
    id: 'export',
    label: 'Export',
    description: 'Export aggregated data to desired format',
  },
]

function App() {
  const [runId, setRunId] = useState<string | null>(null)
  const { run, isLoading, createRun } = useRun(runId)
  const { unlockStage } = useStageAction(runId || '')

  const handleCreateRun = async () => {
    const newRun = await createRun()
    setRunId(newRun.run_id)
  }

  const currentStage = (run?.current_stage || 'selection') as Stage
  const stageIndex = STAGES.findIndex(s => s.id === currentStage)

  // Compute stage states for the wizard
  const stageStates = useMemo<Record<string, StageState>>(() => {
    const states: Record<string, StageState> = {}
    STAGES.forEach((stage, idx) => {
      if (idx < stageIndex) {
        states[stage.id] = 'completed'
      } else if (idx === stageIndex) {
        states[stage.id] = 'active'
      } else {
        states[stage.id] = 'locked'
      }
    })
    return states
  }, [stageIndex])

  // Handle navigating back to a previous stage (per ADR-0001: backward cascade)
  const handleStageClick = async (targetStageId: string) => {
    const targetIndex = STAGES.findIndex(s => s.id === targetStageId)
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
      const prevStage = STAGES[stageIndex - 1]
      handleStageClick(prevStage.id)
    }
  }

  // Render the current stage panel
  const renderStagePanel = () => {
    if (!runId) return null
    switch (currentStage) {
      case 'selection':
        return <SelectionPanel runId={runId} />
      case 'context':
        return <ContextPanel runId={runId} />
      case 'table_availability':
        return <TableAvailabilityPanel runId={runId} />
      case 'table_selection':
        return <TableSelectionPanel runId={runId} />
      case 'preview':
        return <PreviewPanel runId={runId} />
      case 'parse':
        return <ParsePanel runId={runId} />
      case 'export':
        return <ExportPanel runId={runId} />
      default:
        return null
    }
  }

  return (
    <DebugProvider>
      <div className="min-h-screen bg-slate-50 flex flex-col">
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

        {/* Main Content */}
        {!runId ? (
          // Landing page - no run created yet
          <main className="flex-1 flex items-center justify-center p-6">
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
          </main>
        ) : isLoading ? (
          // Loading state
          <main className="flex-1 flex items-center justify-center">
            <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
          </main>
        ) : (
          // Horizontal Wizard - active run
          <DATWizard
            stages={STAGES}
            currentStageId={currentStage}
            stageStates={stageStates}
            onStageClick={handleStageClick}
            onBack={handleBack}
            isLoading={unlockStage.isPending}
          >
            {renderStagePanel()}
          </DATWizard>
        )}

        <DebugPanel />
      </div>
    </DebugProvider>
  )
}

export default App
