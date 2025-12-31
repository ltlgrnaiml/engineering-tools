import { useState } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'
import { SidebarTabs } from './SidebarTabs'
import { ArtifactList } from './ArtifactList'
import type { ArtifactType, ArtifactSummary } from './types'

interface WorkflowSidebarProps {
  onArtifactSelect: (artifact: ArtifactSummary) => void
  selectedArtifactId?: string
}

export function WorkflowSidebar({ onArtifactSelect, selectedArtifactId }: WorkflowSidebarProps) {
  const [collapsed, setCollapsed] = useState(false)
  const [activeTab, setActiveTab] = useState<ArtifactType>('adr')
  const [searchQuery, setSearchQuery] = useState('')

  return (
    <div
      className={cn(
        'flex flex-col border-r border-zinc-800 bg-zinc-900 transition-all duration-200',
        collapsed ? 'w-12' : 'w-72'
      )}
    >
      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center justify-center h-10 border-b border-zinc-800 hover:bg-zinc-800"
      >
        {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
      </button>

      {!collapsed && (
        <>
          <SidebarTabs activeTab={activeTab} onTabChange={setActiveTab} />
          <ArtifactList
            type={activeTab}
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            onSelect={onArtifactSelect}
            selectedId={selectedArtifactId}
          />
        </>
      )}
    </div>
  )
}
