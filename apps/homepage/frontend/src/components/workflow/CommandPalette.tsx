import { useState, useEffect, useMemo } from 'react'
import { Search, FileJson, FileText, MessageSquare, ListTodo, Code2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ArtifactSummary, ArtifactType } from './types'

const TYPE_ICONS: Record<ArtifactType, React.ReactNode> = {
  discussion: <MessageSquare size={14} />,
  adr: <FileJson size={14} />,
  spec: <FileText size={14} />,
  plan: <ListTodo size={14} />,
  contract: <Code2 size={14} />,
}

interface CommandPaletteProps {
  isOpen: boolean
  onClose: () => void
  artifacts: ArtifactSummary[]
  onSelect: (artifact: ArtifactSummary) => void
  recentIds?: string[]
}

export function CommandPalette({ isOpen, onClose, artifacts, onSelect, recentIds = [] }: CommandPaletteProps) {
  const [query, setQuery] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)

  const filtered = useMemo(() => {
    const q = query.toLowerCase()
    let results = artifacts.filter(a => a.id.toLowerCase().includes(q) || a.title.toLowerCase().includes(q))
    // Prioritize recent
    if (recentIds.length && !query) {
      const recent = recentIds.map(id => artifacts.find(a => a.id === id)).filter(Boolean) as ArtifactSummary[]
      results = [...recent, ...results.filter(a => !recentIds.includes(a.id))]
    }
    return results.slice(0, 20)
  }, [artifacts, query, recentIds])

  useEffect(() => {
    setSelectedIndex(0)
  }, [query])

  useEffect(() => {
    if (!isOpen) { setQuery(''); setSelectedIndex(0) }
  }, [isOpen])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return
      if (e.key === 'ArrowDown') { e.preventDefault(); setSelectedIndex(i => Math.min(i + 1, filtered.length - 1)) }
      if (e.key === 'ArrowUp') { e.preventDefault(); setSelectedIndex(i => Math.max(i - 1, 0)) }
      if (e.key === 'Enter' && filtered[selectedIndex]) {
        onSelect(filtered[selectedIndex])
        onClose()
      }
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, filtered, selectedIndex, onSelect, onClose])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]" onClick={onClose}>
      <div className="absolute inset-0 bg-black/60" />
      <div
        onClick={(e) => e.stopPropagation()}
        className="relative w-[560px] bg-zinc-900 border border-zinc-700 rounded-xl shadow-2xl overflow-hidden"
      >
        <div className="flex items-center gap-3 px-4 py-3 border-b border-zinc-800">
          <Search size={18} className="text-zinc-400" />
          <input
            autoFocus
            type="text"
            placeholder="Search artifacts..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 bg-transparent outline-none text-lg"
          />
        </div>
        <div className="max-h-80 overflow-auto">
          {filtered.length === 0 ? (
            <div className="p-4 text-zinc-500 text-center">No results</div>
          ) : (
            filtered.map((artifact, i) => (
              <button
                key={artifact.id}
                onClick={() => { onSelect(artifact); onClose() }}
                className={cn(
                  'w-full flex items-center gap-3 px-4 py-2.5 text-left',
                  i === selectedIndex ? 'bg-blue-600/20' : 'hover:bg-zinc-800'
                )}
              >
                <span className="text-zinc-400">{TYPE_ICONS[artifact.type]}</span>
                <span className="font-medium">{artifact.id}</span>
                <span className="text-zinc-500 truncate">{artifact.title}</span>
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
