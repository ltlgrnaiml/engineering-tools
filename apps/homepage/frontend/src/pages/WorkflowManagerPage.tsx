import { useState, useEffect, useCallback } from 'react'
import {
  WorkflowSidebar,
  ArtifactGraph,
  ArtifactReader,
  ArtifactEditor,
  WorkflowHeader,
  CommandPalette,
  WorkflowStepper,
  EmptyState,
} from '@/components/workflow'
import { useWorkflowState } from '@/components/workflow/useWorkflowState'
import type { ArtifactType, ArtifactSummary } from '@/components/workflow/types'

const API_BASE = 'http://localhost:8000/api/devtools'

export function WorkflowManagerPage() {
  const [selectedArtifact, setSelectedArtifact] = useState<{ id: string; type: ArtifactType; filePath: string } | null>(null)
  const [editorOpen, setEditorOpen] = useState(false)
  const [paletteOpen, setPaletteOpen] = useState(false)
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

  const handleArtifactSelect = useCallback((id: string, type: ArtifactType) => {
    const artifact = allArtifacts.find(a => a.id === id)
    if (artifact) {
      setSelectedArtifact({ id, type, filePath: artifact.file_path })
      setEditorOpen(false)
    }
  }, [allArtifacts])

  const handleNewWorkflow = useCallback((type: string) => {
    workflow.startWorkflow(type)
  }, [workflow])

  return (
    <div className="flex flex-col h-screen bg-zinc-950 text-white">
      {/* Workflow Stepper */}
      {workflow.workflowType && (
        <WorkflowStepper
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
      <div className="flex items-center gap-2 px-4 py-2 border-b border-zinc-800">
        <button
          onClick={() => setView('list')}
          className={`px-3 py-1 rounded ${view === 'list' ? 'bg-zinc-700' : 'hover:bg-zinc-800'}`}
        >
          List
        </button>
        <button
          onClick={() => setView('graph')}
          className={`px-3 py-1 rounded ${view === 'graph' ? 'bg-zinc-700' : 'hover:bg-zinc-800'}`}
        >
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
              onNodeClick={handleArtifactSelect}
              selectedNodeId={selectedArtifact?.id}
              className="flex-1"
            />
          ) : selectedArtifact ? (
            <ArtifactReader
              artifactId={selectedArtifact.id}
              artifactType={selectedArtifact.type}
              filePath={selectedArtifact.filePath}
              onEdit={() => setEditorOpen(true)}
              className="flex-1"
            />
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
    </div>
  )
}
