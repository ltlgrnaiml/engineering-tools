import { MessageSquare, FileJson, FileText, ListTodo, Code2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ArtifactType } from './types'

const TABS: { type: ArtifactType; icon: React.ReactNode; label: string }[] = [
  { type: 'discussion', icon: <MessageSquare size={16} />, label: 'Discussions' },
  { type: 'adr', icon: <FileJson size={16} />, label: 'ADRs' },
  { type: 'spec', icon: <FileText size={16} />, label: 'SPECs' },
  { type: 'plan', icon: <ListTodo size={16} />, label: 'Plans' },
  { type: 'contract', icon: <Code2 size={16} />, label: 'Contracts' },
]

interface SidebarTabsProps {
  activeTab: ArtifactType
  onTabChange: (tab: ArtifactType) => void
}

export function SidebarTabs({ activeTab, onTabChange }: SidebarTabsProps) {
  return (
    <div className="flex border-b border-zinc-800">
      {TABS.map(({ type, icon, label }) => (
        <button
          key={type}
          onClick={() => onTabChange(type)}
          title={label}
          className={cn(
            'flex-1 flex items-center justify-center py-2 hover:bg-zinc-800 transition-colors',
            activeTab === type && 'bg-zinc-800 border-b-2 border-blue-500'
          )}
        >
          {icon}
        </button>
      ))}
    </div>
  )
}
