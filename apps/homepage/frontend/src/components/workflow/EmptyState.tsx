import { Plus, FileJson, FileText, MessageSquare, ListTodo, Code2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ArtifactType } from './types'

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
