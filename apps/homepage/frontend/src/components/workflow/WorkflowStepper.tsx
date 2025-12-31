import { Check, ArrowRight } from 'lucide-react'
import { cn } from '@/lib/utils'

export type WorkflowStage = 'discussion' | 'adr' | 'spec' | 'contract' | 'plan' | 'fragment'
export type WorkflowType = 'feature' | 'bugfix' | 'refactor' | 'enhancement'

const ALL_STAGES: { id: WorkflowStage; label: string; description: string }[] = [
  { id: 'discussion', label: 'Discussion', description: 'Capture design conversation' },
  { id: 'adr', label: 'ADR', description: 'Record architecture decision' },
  { id: 'spec', label: 'SPEC', description: 'Define requirements' },
  { id: 'contract', label: 'Contract', description: 'Create data shapes' },
  { id: 'plan', label: 'Plan', description: 'Break into tasks' },
  { id: 'fragment', label: 'Fragment', description: 'Execute & verify' },
]

// Define which stages each workflow type uses
const WORKFLOW_STAGES: Record<WorkflowType, WorkflowStage[]> = {
  feature: ['discussion', 'adr', 'spec', 'contract', 'plan', 'fragment'],
  bugfix: ['plan', 'fragment'],
  refactor: ['adr', 'plan', 'fragment'],
  enhancement: ['spec', 'plan', 'fragment'],
}

// Get the starting stage for a workflow type
export function getStartingStage(workflowType: WorkflowType): WorkflowStage {
  return WORKFLOW_STAGES[workflowType][0]
}

// Get stages for a workflow type
export function getWorkflowStages(workflowType: WorkflowType): WorkflowStage[] {
  return WORKFLOW_STAGES[workflowType]
}

// Check if a stage is included in a workflow type
export function isStageInWorkflow(stage: WorkflowStage, workflowType: WorkflowType): boolean {
  return WORKFLOW_STAGES[workflowType].includes(stage)
}

// Map artifact types to workflow stages
export function artifactTypeToStage(artifactType: string): WorkflowStage | null {
  const mapping: Record<string, WorkflowStage> = {
    discussion: 'discussion',
    adr: 'adr',
    spec: 'spec',
    contract: 'contract',
    plan: 'plan',
  }
  return mapping[artifactType.toLowerCase()] || null
}

interface WorkflowStepperProps {
  workflowType: WorkflowType
  currentStage: WorkflowStage
  completedStages: WorkflowStage[]
  onStageClick?: (stage: WorkflowStage) => void
  className?: string
}

export function WorkflowStepper({ workflowType, currentStage, completedStages, onStageClick, className }: WorkflowStepperProps) {
  // Filter stages based on workflow type
  const stageIds = WORKFLOW_STAGES[workflowType]
  const stages = ALL_STAGES.filter(s => stageIds.includes(s.id))
  const currentIndex = stages.findIndex(s => s.id === currentStage)

  return (
    <div className={cn('flex items-center gap-2 p-4 bg-zinc-900 border-b border-zinc-800 overflow-x-auto', className)}>
      {stages.map((stage, index) => {
        const isCompleted = completedStages.includes(stage.id)
        const isCurrent = stage.id === currentStage
        // isPast can be used for styling past steps differently
        void (index < currentIndex)

        return (
          <div key={stage.id} className="flex items-center">
            <button
              onClick={() => onStageClick?.(stage.id)}
              disabled={!isCompleted && !isCurrent}
              className={cn(
                'flex items-center gap-2 px-3 py-2 rounded-lg transition-colors',
                isCurrent && 'bg-blue-600/20 border border-blue-500',
                isCompleted && 'hover:bg-zinc-800',
                !isCompleted && !isCurrent && 'opacity-50 cursor-not-allowed'
              )}
            >
              <div
                className={cn(
                  'w-6 h-6 rounded-full flex items-center justify-center text-xs',
                  isCompleted ? 'bg-green-500' : isCurrent ? 'bg-blue-500' : 'bg-zinc-700'
                )}
              >
                {isCompleted ? <Check size={14} /> : index + 1}
              </div>
              <div className="text-left hidden sm:block">
                <div className="text-sm font-medium">{stage.label}</div>
                <div className="text-xs text-zinc-500">{stage.description}</div>
              </div>
            </button>
            {index < stages.length - 1 && (
              <ArrowRight size={16} className="mx-2 text-zinc-600" />
            )}
          </div>
        )
      })}
    </div>
  )
}
