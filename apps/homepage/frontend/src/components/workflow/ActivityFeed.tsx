import { Clock, FileJson, FileText, MessageSquare, ListTodo, Code2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ArtifactType, ArtifactSummary } from './types'

const TYPE_ICONS: Record<ArtifactType, React.ReactNode> = {
  discussion: <MessageSquare size={14} />,
  adr: <FileJson size={14} />,
  spec: <FileText size={14} />,
  plan: <ListTodo size={14} />,
  contract: <Code2 size={14} />,
}

interface ActivityFeedProps {
  recentArtifacts: ArtifactSummary[]
  onSelect: (id: string, type: ArtifactType) => void
  className?: string
}

export function ActivityFeed({ recentArtifacts, onSelect, className }: ActivityFeedProps) {
  return (
    <div className={cn('flex flex-col', className)}>
      <div className="flex items-center gap-2 px-4 py-2 border-b border-zinc-800">
        <Clock size={14} className="text-zinc-400" />
        <h3 className="text-sm font-medium text-zinc-400">Recent Activity</h3>
      </div>
      <div className="flex-1 overflow-auto">
        {recentArtifacts.length === 0 ? (
          <div className="p-4 text-sm text-zinc-500 text-center">No recent activity</div>
        ) : (
          recentArtifacts.map((artifact) => (
            <button
              key={artifact.id}
              onClick={() => onSelect(artifact.id, artifact.type)}
              className="w-full flex items-center gap-3 px-4 py-2 hover:bg-zinc-800 text-left border-b border-zinc-800/50"
            >
              <span className="text-zinc-400">{TYPE_ICONS[artifact.type]}</span>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium truncate">{artifact.id}</div>
                <div className="text-xs text-zinc-500 truncate">{artifact.title}</div>
              </div>
              {artifact.updated_date && (
                <span className="text-xs text-zinc-500">{artifact.updated_date}</span>
              )}
            </button>
          ))
        )}
      </div>
    </div>
  )
}
