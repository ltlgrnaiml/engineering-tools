import { Plus, FileJson, FileText, MessageSquare, ListTodo, Code2, Sparkles, ArrowRight } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ArtifactType } from './types'
import type { WorkflowStage, WorkflowType } from './workflowUtils'

const EMPTY_STATE_CONTENT: Record<ArtifactType, { icon: React.ReactNode; title: string; description: string; cta: string }> = {
  discussion: {
    icon: <MessageSquare size={48} className="text-purple-400" />,
    title: 'No discussions yet',
    description: 'Discussions capture design conversations before making decisions.',
    cta: 'Start a Discussion',
  },
  adr: {
    icon: <FileJson size={48} className="text-blue-400" />,
    title: 'No ADRs yet',
    description: 'Architecture Decision Records document the "why" behind decisions.',
    cta: 'Create an ADR',
  },
  spec: {
    icon: <FileText size={48} className="text-green-400" />,
    title: 'No SPECs yet',
    description: 'Specifications define the "what" - behavioral requirements and acceptance criteria.',
    cta: 'Write a SPEC',
  },
  plan: {
    icon: <ListTodo size={48} className="text-amber-400" />,
    title: 'No plans yet',
    description: 'Plans break work into milestones and tasks with verification commands.',
    cta: 'Create a Plan',
  },
  contract: {
    icon: <Code2 size={48} className="text-pink-400" />,
    title: 'No contracts yet',
    description: 'Contracts define data shapes as Pydantic models.',
    cta: 'Add a Contract',
  },
}

const STAGE_TO_ARTIFACT: Record<WorkflowStage, ArtifactType> = {
  discussion: 'discussion',
  adr: 'adr',
  spec: 'spec',
  contract: 'contract',
  plan: 'plan',
  fragment: 'plan', // Fragment uses plan as base
}

const WORKFLOW_NAMES: Record<WorkflowType, string> = {
  feature: 'New Feature',
  bugfix: 'Bug Fix',
  refactor: 'Refactor',
  enhancement: 'Enhancement',
}

interface EmptyStateProps {
  type: ArtifactType
  onAction: () => void
  className?: string
}

export function EmptyState({ type, onAction, className }: EmptyStateProps) {
  const content = EMPTY_STATE_CONTENT[type]

  return (
    <div className={cn('flex flex-col items-center justify-center h-full p-8 text-center', className)}>
      {content.icon}
      <h2 className="mt-4 text-xl font-semibold">{content.title}</h2>
      <p className="mt-2 text-sm text-zinc-400 max-w-md">{content.description}</p>
      <button
        onClick={onAction}
        className="mt-6 flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg"
      >
        <Plus size={16} />
        {content.cta}
      </button>
    </div>
  )
}

interface WorkflowStartedStateProps {
  workflowType: WorkflowType
  currentStage: WorkflowStage
  onCreateArtifact: () => void
  onCopyPrompt: () => void
  className?: string
}

export function WorkflowStartedState({ 
  workflowType, 
  currentStage, 
  onCreateArtifact, 
  onCopyPrompt,
  className 
}: WorkflowStartedStateProps) {
  const artifactType = STAGE_TO_ARTIFACT[currentStage]
  const content = EMPTY_STATE_CONTENT[artifactType]
  const workflowName = WORKFLOW_NAMES[workflowType]

  return (
    <div className={cn('flex flex-col items-center justify-center h-full p-8 text-center', className)}>
      <div className="mb-4 px-3 py-1 bg-blue-600/20 border border-blue-500/30 rounded-full text-blue-400 text-sm">
        {workflowName} Workflow Started
      </div>
      
      {content.icon}
      
      <h2 className="mt-4 text-xl font-semibold">
        Step 1: Create a {currentStage.toUpperCase()}
      </h2>
      <p className="mt-2 text-sm text-zinc-400 max-w-md">
        {content.description}
      </p>

      <div className="mt-6 flex flex-col sm:flex-row items-center gap-3">
        <button
          onClick={onCopyPrompt}
          className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg"
        >
          <Sparkles size={16} />
          Copy AI Prompt
        </button>
        <span className="text-zinc-500 text-sm">or</span>
        <button
          onClick={onCreateArtifact}
          className="flex items-center gap-2 px-4 py-2 bg-zinc-700 hover:bg-zinc-600 rounded-lg"
        >
          <Plus size={16} />
          Create Manually
        </button>
      </div>

      <div className="mt-8 flex items-center gap-2 text-xs text-zinc-500">
        <span>After creating, click</span>
        <span className="px-2 py-1 bg-zinc-800 rounded">Copy AI Prompt</span>
        <ArrowRight size={12} />
        <span>to get the next step</span>
      </div>
    </div>
  )
}
