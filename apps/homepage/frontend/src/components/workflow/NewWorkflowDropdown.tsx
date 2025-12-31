import { useState, useRef, useEffect } from 'react'
import { Plus, ChevronDown, Sparkles, Bug, Wrench, FileText, Wand2 } from 'lucide-react'

const WORKFLOW_TYPES = [
  { id: 'ai_full', label: 'AI-Full Mode ✨', icon: Wand2, description: 'One-click: Generate all artifacts automatically', highlight: true },
  { id: 'feature', label: 'New Feature', icon: Sparkles, description: 'Manual: Discussion → ADR → SPEC → Plan' },
  { id: 'bugfix', label: 'Bug Fix', icon: Bug, description: 'Manual: Plan → Fragment' },
  { id: 'refactor', label: 'Refactor', icon: Wrench, description: 'Manual: ADR → Plan' },
  { id: 'enhancement', label: 'Enhancement', icon: FileText, description: 'Manual: SPEC → Plan' },
]

interface NewWorkflowDropdownProps {
  onSelect: (type: string) => void
}

export function NewWorkflowDropdown({ onSelect }: NewWorkflowDropdownProps) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 rounded text-sm"
      >
        <Plus size={14} />
        New Workflow
        <ChevronDown size={14} />
      </button>

      {open && (
        <div className="absolute right-0 mt-1 w-72 bg-zinc-800 border border-zinc-700 rounded-lg shadow-xl z-50">
          {WORKFLOW_TYPES.map(({ id, label, icon: Icon, description, highlight }) => (
            <button
              key={id}
              onClick={() => { onSelect(id); setOpen(false) }}
              className={`w-full flex items-start gap-3 px-3 py-2.5 first:rounded-t-lg last:rounded-b-lg text-left ${
                highlight 
                  ? 'bg-purple-600/20 hover:bg-purple-600/30 border-b border-purple-500/30' 
                  : 'hover:bg-zinc-700'
              }`}
            >
              <Icon size={18} className={`mt-0.5 ${highlight ? 'text-purple-400' : 'text-zinc-400'}`} />
              <div>
                <div className={`font-medium ${highlight ? 'text-purple-300' : ''}`}>{label}</div>
                <div className="text-xs text-zinc-400">{description}</div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
