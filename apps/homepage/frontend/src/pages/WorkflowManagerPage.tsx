import { useState, useEffect, useCallback } from 'react'
import { List, Network } from 'lucide-react'
import {
  WorkflowSidebar,
  ArtifactGraph,
  ArtifactReader,
  ArtifactEditor,
  WorkflowHeader,
  CommandPalette,
  WorkflowStepper,
  EmptyState,
  WorkflowStartedState,
  GenerateWorkflowModal,
} from '@/components/workflow'
import { useWorkflowState } from '@/components/workflow/useWorkflowState'
import type { ArtifactType, FileFormat, ArtifactSummary } from '@/components/workflow/types'
import type { WorkflowType } from '@/components/workflow/workflowUtils'
import { isStageInWorkflow, artifactTypeToStage } from '@/components/workflow/workflowUtils'

const API_BASE = 'http://localhost:8000/api/devtools'

export function WorkflowManagerPage() {
  const [selectedArtifact, setSelectedArtifact] = useState<{ id: string; type: ArtifactType; filePath: string; fileFormat: FileFormat } | null>(null)
  const [editorOpen, setEditorOpen] = useState(false)
  const [paletteOpen, setPaletteOpen] = useState(false)
  const [generateModalOpen, setGenerateModalOpen] = useState(false)
  const [allArtifacts, setAllArtifacts] = useState<ArtifactSummary[]>([])
  const [view, setView] = useState<'list' | 'graph'>('list')

  const workflow = useWorkflowState()

  // Fetch all artifacts for command palette
  useEffect(() => {
    fetch(`${API_BASE}/artifacts`)
      .then(res => res.json())
      .then(data => setAllArtifacts(data.items || []))
      .catch(console.error)
  }, [])

  // Global Cmd+K listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setPaletteOpen(true)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  const handleArtifactSelect = useCallback((artifact: ArtifactSummary) => {
    setSelectedArtifact({
      id: artifact.id,
      type: artifact.type,
      filePath: artifact.file_path,
      fileFormat: artifact.file_format || 'unknown'
    })
    setEditorOpen(false)
  }, [])

  // Graph nodes don't have file_format, so we need a separate handler
  const handleGraphNodeClick = useCallback((nodeId: string, type: ArtifactType) => {
    // Find the artifact in allArtifacts for file_format, fallback to 'unknown'
    const artifact = allArtifacts.find(a => a.id === nodeId)
    setSelectedArtifact({
      id: nodeId,
      type,
      filePath: artifact?.file_path || '',
      fileFormat: artifact?.file_format || 'unknown'
    })
    setEditorOpen(false)
  }, [allArtifacts])

  const handleNewWorkflow = useCallback((type: string) => {
    // Warn user if they have an active workflow or selected artifact
    if (workflow.workflowType || selectedArtifact) {
      let msg = workflow.workflowType 
        ? 'Starting a new workflow will reset your current workflow progress.'
        : 'Starting a new workflow will clear your current selection.'
      
      // Check for workflow type mismatch with selected artifact
      if (selectedArtifact && type !== 'ai_full') {
        const selectedStage = artifactTypeToStage(selectedArtifact.type)
        if (selectedStage && !isStageInWorkflow(selectedStage, type as WorkflowType)) {
          msg += `\n\nNote: Your selected ${selectedArtifact.type.toUpperCase()} artifact is not part of the "${type}" workflow.`
        }
      }
      
      msg += '\n\nContinue?'
      
      if (!window.confirm(msg)) {
        return
      }
      // Reset current state
      setSelectedArtifact(null)
      setEditorOpen(false)
    }
    
    if (type === 'ai_full') {
      setGenerateModalOpen(true)
    } else {
      workflow.startWorkflow(type as WorkflowType)
    }
  }, [workflow, selectedArtifact])

  return (
    <div className="flex flex-col h-screen bg-zinc-950 text-white">
      {/* Workflow Stepper */}
      {workflow.workflowType && (
        <WorkflowStepper
          workflowType={workflow.workflowType}
          currentStage={workflow.currentStage}
          completedStages={workflow.completedStages}
        />
      )}

      {/* Header */}
      <WorkflowHeader
        onOpenCommandPalette={() => setPaletteOpen(true)}
        onNewWorkflow={handleNewWorkflow}
      />

      {/* View Toggle */}
      <div className="flex items-center gap-1 px-4 py-2 border-b border-zinc-800">
        <span className="text-xs text-zinc-500 mr-2">View:</span>
        <button
          onClick={() => setView('list')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-sm transition-colors ${
            view === 'list' 
              ? 'bg-blue-600 text-white' 
              : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-white'
          }`}
        >
          <List size={14} />
          List
        </button>
        <button
          onClick={() => setView('graph')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-sm transition-colors ${
            view === 'graph' 
              ? 'bg-blue-600 text-white' 
              : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-white'
          }`}
        >
          <Network size={14} />
          Graph
        </button>
      </div>

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <WorkflowSidebar
          onArtifactSelect={handleArtifactSelect}
          selectedArtifactId={selectedArtifact?.id}
        />

        {/* Main panel */}
        <div className="flex-1 flex">
          {view === 'graph' ? (
            <ArtifactGraph
              onNodeClick={handleGraphNodeClick}
              selectedNodeId={selectedArtifact?.id}
              className="flex-1"
            />
          ) : selectedArtifact ? (
            <ArtifactReader
              artifactId={selectedArtifact.id}
              artifactType={selectedArtifact.type}
              fileFormat={selectedArtifact.fileFormat}
              filePath={selectedArtifact.filePath}
              onEdit={() => setEditorOpen(true)}
              className="flex-1"
            />
          ) : workflow.workflowType ? (
            <div className="flex-1 flex items-center justify-center">
              <WorkflowStartedState
                workflowType={workflow.workflowType}
                currentStage={workflow.currentStage}
                onCreateArtifact={() => {
                  // TODO: Open editor for new artifact
                  console.log('Create artifact for stage:', workflow.currentStage)
                }}
                onCopyPrompt={() => {
                  // Copy a starter prompt for the current stage
                  const stagePrompts: Record<string, string> = {
                    discussion: `Create a new Discussion file for this feature.\n\nTemplate:\n# DISC-XXX: [Title]\n\n## Summary\n[One paragraph describing the feature]\n\n## Requirements\n### Functional Requirements\n- [ ] **FR-1**: [Requirement]\n\n## Open Questions\n| ID | Question | Status |\n|----|----------|--------|\n| Q-1 | [Question] | open |`,
                    adr: 'Create an ADR (Architecture Decision Record) that documents the key architectural decision for this work. Include context, decision, consequences, and alternatives considered.',
                    spec: 'Create a SPEC that defines the functional requirements, API contracts, and acceptance criteria for this feature.',
                    plan: 'Create a Plan that breaks this work into milestones and tasks with verification commands.',
                    contract: 'Create Pydantic contracts that define the data shapes needed for this feature.',
                  }
                  const prompt = stagePrompts[workflow.currentStage] || 'Create the next artifact for this workflow.'
                  navigator.clipboard.writeText(prompt)
                  alert('Prompt copied to clipboard! Paste it into your AI assistant.')
                }}
              />
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <EmptyState type="adr" onAction={() => handleNewWorkflow('feature')} />
            </div>
          )}
        </div>
      </div>

      {/* Editor slide-in */}
      {selectedArtifact && (
        <ArtifactEditor
          artifactId={selectedArtifact.id}
          artifactType={selectedArtifact.type}
          isOpen={editorOpen}
          onClose={() => setEditorOpen(false)}
        />
      )}

      {/* Command palette */}
      <CommandPalette
        isOpen={paletteOpen}
        onClose={() => setPaletteOpen(false)}
        artifacts={allArtifacts}
        onSelect={handleArtifactSelect}
      />

      {/* AI-Full Mode Generate Modal */}
      <GenerateWorkflowModal
        isOpen={generateModalOpen}
        onClose={() => setGenerateModalOpen(false)}
        onSuccess={(artifacts) => {
          // Refresh artifact list and select first generated artifact
          fetch(`${API_BASE}/artifacts`)
            .then(res => res.json())
            .then(data => {
              const items: ArtifactSummary[] = data.items || []
              setAllArtifacts(items)
              if (artifacts.length > 0) {
                // Find full artifact in refreshed list
                const fullArtifact = items.find(a => a.id === artifacts[0].id)
                if (fullArtifact) {
                  handleArtifactSelect(fullArtifact)
                }
              }
            })
        }}
      />
    </div>
  )
}
