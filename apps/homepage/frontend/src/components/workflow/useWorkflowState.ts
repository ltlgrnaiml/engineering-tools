import { useState, useEffect, useCallback } from 'react'
import type { WorkflowStage, WorkflowType } from './workflowUtils'
import { getStartingStage } from './workflowUtils'

const STORAGE_KEY = 'workflow-manager-state'

interface WorkflowState {
  workflowType: WorkflowType | null
  currentStage: WorkflowStage
  completedStages: WorkflowStage[]
  artifactIds: Record<WorkflowStage, string | null>
  startedAt: string | null
}

const DEFAULT_STATE: WorkflowState = {
  workflowType: null,
  currentStage: 'discussion',
  completedStages: [],
  artifactIds: { discussion: null, adr: null, spec: null, contract: null, plan: null, fragment: null },
  startedAt: null,
}

export function useWorkflowState() {
  const [state, setState] = useState<WorkflowState>(DEFAULT_STATE)

  // Load from sessionStorage on mount
  useEffect(() => {
    const saved = sessionStorage.getItem(STORAGE_KEY)
    if (saved) {
      try {
        setState(JSON.parse(saved))
      } catch {
        sessionStorage.removeItem(STORAGE_KEY)
      }
    }
  }, [])

  // Persist to sessionStorage on change
  useEffect(() => {
    if (state.workflowType) {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state))
    }
  }, [state])

  const startWorkflow = useCallback((type: WorkflowType) => {
    const startingStage = getStartingStage(type)
    setState({
      ...DEFAULT_STATE,
      workflowType: type,
      currentStage: startingStage,
      startedAt: new Date().toISOString(),
    })
  }, [])

  const advanceStage = useCallback((artifactId: string) => {
    setState(prev => {
      const stages: WorkflowStage[] = ['discussion', 'adr', 'spec', 'contract', 'plan', 'fragment']
      const currentIndex = stages.indexOf(prev.currentStage)
      const nextStage = stages[currentIndex + 1] || prev.currentStage

      return {
        ...prev,
        completedStages: [...prev.completedStages, prev.currentStage],
        artifactIds: { ...prev.artifactIds, [prev.currentStage]: artifactId },
        currentStage: nextStage,
      }
    })
  }, [])

  const resetWorkflow = useCallback(() => {
    setState(DEFAULT_STATE)
    sessionStorage.removeItem(STORAGE_KEY)
  }, [])

  return { ...state, startWorkflow, advanceStage, resetWorkflow }
}
