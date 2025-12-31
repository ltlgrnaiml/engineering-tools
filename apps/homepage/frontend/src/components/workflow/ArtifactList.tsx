import { Search, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useArtifacts } from '@/hooks/useWorkflowApi'
import type { ArtifactType, ArtifactSummary } from './types'

interface ArtifactListProps {
  type: ArtifactType
  searchQuery: string
  onSearchChange: (query: string) => void
  onSelect: (artifact: ArtifactSummary) => void
  selectedId?: string
}

export function ArtifactList({
  type,
  searchQuery,
  onSearchChange,
  onSelect,
  selectedId,
}: ArtifactListProps) {
  const { data: artifacts, loading, error } = useArtifacts(type, searchQuery)

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      {/* Search input */}
      <div className="p-2 border-b border-zinc-800">
        <div className="relative">
          <Search size={14} className="absolute left-2 top-1/2 -translate-y-1/2 text-zinc-500" />
          <input
            type="text"
            placeholder="Search..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full pl-7 pr-2 py-1 text-sm bg-zinc-800 border border-zinc-700 rounded focus:outline-none focus:border-blue-500"
          />
        </div>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto">
        {loading && (
          <div className="flex items-center justify-center py-8">
            <Loader2 size={20} className="animate-spin text-zinc-500" />
          </div>
        )}
        
        {error && (
          <div className="p-4 text-red-400 text-sm">{error.message}</div>
        )}
        
        {!loading && !error && artifacts?.map((artifact) => (
          <button
            key={artifact.id}
            onClick={() => onSelect(artifact)}
            className={cn(
              'w-full text-left px-3 py-2 text-sm hover:bg-zinc-800 border-b border-zinc-800/50',
              selectedId === artifact.id && 'bg-zinc-800'
            )}
          >
            <div className="font-medium truncate">{artifact.id}</div>
            <div className="text-xs text-zinc-500 truncate">{artifact.title}</div>
          </button>
        ))}
        
        {!loading && !error && (!artifacts || artifacts.length === 0) && (
          <div className="p-4 text-zinc-500 text-sm text-center">No artifacts found</div>
        )}
      </div>
    </div>
  )
}
