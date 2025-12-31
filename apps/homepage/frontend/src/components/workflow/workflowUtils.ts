/**
 * Workflow utility functions and types.
 * Separated from WorkflowStepper component for React Fast Refresh compatibility.
 */

export type WorkflowStage = 'discussion' | 'adr' | 'spec' | 'contract' | 'plan' | 'fragment'
export type WorkflowType = 'feature' | 'bugfix' | 'refactor' | 'enhancement'

export const ALL_STAGES: { id: WorkflowStage; label: string; description: string }[] = [
  { id: 'discussion', label: 'Discussion', description: 'Capture design conversation' },
  { id: 'adr', label: 'ADR', description: 'Record architecture decision' },
  { id: 'spec', label: 'SPEC', description: 'Define requirements' },
  { id: 'contract', label: 'Contract', description: 'Create data shapes' },
  { id: 'plan', label: 'Plan', description: 'Break into tasks' },
  { id: 'fragment', label: 'Fragment', description: 'Execute & verify' },
]

// Define which stages each workflow type uses
export const WORKFLOW_STAGES: Record<WorkflowType, WorkflowStage[]> = {
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
