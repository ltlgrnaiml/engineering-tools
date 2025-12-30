import { Search, Settings } from 'lucide-react'
import { cn } from '@/lib/utils'
import { NewWorkflowDropdown } from './NewWorkflowDropdown'

interface WorkflowHeaderProps {
  onOpenCommandPalette: () => void
  onNewWorkflow: (type: string) => void
  className?: string
}

export function WorkflowHeader({ onOpenCommandPalette, onNewWorkflow, className }: WorkflowHeaderProps) {
  return (
    <div className={cn('flex items-center justify-between px-4 py-2 border-b border-zinc-800 bg-zinc-900', className)}>
      <div className="flex items-center gap-4">
        <h1 className="text-lg font-semibold">Workflow Manager</h1>
        <button
          onClick={onOpenCommandPalette}
          className="flex items-center gap-2 px-3 py-1.5 text-sm text-zinc-400 bg-zinc-800 hover:bg-zinc-700 rounded border border-zinc-700"
        >
          <Search size={14} />
          <span>Search artifacts...</span>
          <kbd className="ml-4 px-1.5 py-0.5 text-xs bg-zinc-700 rounded">⌘K</kbd>
        </button>
      </div>
      <div className="flex items-center gap-2">
        <NewWorkflowDropdown onSelect={onNewWorkflow} />
        <button className="p-2 hover:bg-zinc-800 rounded" title="Settings">
          <Settings size={16} />
        </button>
      </div>
    </div>
  )
}
