import { cn } from '@/lib/utils'
import { Target, CheckCircle, Circle, Clock, AlertTriangle, Flag } from 'lucide-react'

interface BadgeProps {
  children: React.ReactNode
  className?: string
  variant?: 'default' | 'outline' | 'secondary'
}

function Badge({ children, className, variant = 'default' }: BadgeProps) {
  const variants = {
    default: 'bg-zinc-700 text-white',
    outline: 'border border-zinc-600 text-zinc-300',
    secondary: 'bg-zinc-800 text-zinc-300',
  }
  return (
    <span className={cn('inline-flex items-center px-2 py-0.5 rounded text-xs font-medium', variants[variant], className)}>
      {children}
    </span>
  )
}

interface Task {
  id: string
  description: string
  status: string
  verification_command?: string
  evidence?: string | null
  notes?: string | null
}

interface Milestone {
  id: string
  name?: string  // Actual field name in JSON
  title?: string // Alternative field name
  objective?: string
  status: 'pending' | 'in_progress' | 'completed'
  deliverables?: string[]
  tasks?: Task[]
}

interface PlanData {
  id?: string
  title?: string
  status?: string
  granularity?: string
  objective?: string
  scope?: string
  milestones?: Milestone[]
  global_acceptance_criteria?: string[]
  risks?: string[]
  [key: string]: unknown
}

interface PlanViewerProps {
  content: string
  className?: string
}

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-zinc-600',
  active: 'bg-blue-600',
  completed: 'bg-green-600',
  on_hold: 'bg-amber-600',
}

const MILESTONE_STATUS_ICONS: Record<string, React.ReactNode> = {
  pending: <Circle size={16} className="text-zinc-500" />,
  in_progress: <Clock size={16} className="text-blue-400" />,
  completed: <CheckCircle size={16} className="text-green-500" />,
}

export function PlanViewer({ content, className }: PlanViewerProps) {
  let data: PlanData = {}
  try {
    data = JSON.parse(content)
  } catch {
    return <div className="p-4 text-red-400">Invalid JSON content</div>
  }

  const renderSection = (title: string, children: React.ReactNode) => (
    <section className="mb-6">
      <h3 className="text-lg font-semibold text-zinc-200 mb-2 border-b border-zinc-700 pb-1">{title}</h3>
      {children}
    </section>
  )

  const completedMilestones = data.milestones?.filter(m => m.status === 'completed').length || 0
  const totalMilestones = data.milestones?.length || 0
  const progress = totalMilestones > 0 ? Math.round((completedMilestones / totalMilestones) * 100) : 0

  return (
    <div className={cn('p-6 overflow-auto h-full', className)}>
      {/* Header */}
      <header className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <span className="text-sm font-mono text-zinc-500">{data.id}</span>
          <Badge className={cn('text-white', STATUS_COLORS[data.status || 'draft'])}>
            {data.status || 'draft'}
          </Badge>
          {data.granularity && <Badge variant="outline">L{data.granularity}</Badge>}
        </div>
        <h1 className="text-2xl font-bold text-white mb-3">{data.title}</h1>
        
        {/* Progress Bar */}
        <div className="mt-4">
          <div className="flex justify-between text-sm text-zinc-400 mb-1">
            <span>Progress</span>
            <span>{completedMilestones}/{totalMilestones} milestones ({progress}%)</span>
          </div>
          <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
            <div 
              className="h-full bg-green-500 transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </header>

      {/* Objective */}
      {data.objective && renderSection('Objective',
        <div className="flex items-start gap-3 bg-blue-900/20 border border-blue-700/50 rounded-lg p-4">
          <Target size={20} className="text-blue-400 mt-0.5" />
          <p className="text-blue-200">{data.objective}</p>
        </div>
      )}

      {/* Scope */}
      {data.scope && renderSection('Scope',
        <p className="text-zinc-300 whitespace-pre-wrap">{data.scope}</p>
      )}

      {/* Milestones */}
      {data.milestones?.length ? renderSection('Milestones',
        <div className="space-y-4">
          {data.milestones.map((milestone, i) => (
            <div 
              key={i} 
              className={cn(
                'rounded-lg p-4 border',
                milestone.status === 'completed' ? 'bg-green-900/10 border-green-700/50' :
                milestone.status === 'in_progress' ? 'bg-blue-900/10 border-blue-700/50' :
                'bg-zinc-800/50 border-zinc-700'
              )}
            >
              <div className="flex items-center gap-3 mb-2">
                {MILESTONE_STATUS_ICONS[milestone.status]}
                <Badge variant="outline">{milestone.id}</Badge>
                <span className="font-medium text-zinc-200">{milestone.name || milestone.title}</span>
              </div>
              {milestone.objective && (
                <p className="text-sm text-zinc-400 ml-7 mb-2">{milestone.objective}</p>
              )}
              {milestone.tasks?.length ? (
                <div className="ml-7 mt-3 space-y-2">
                  {milestone.tasks.map((task, j) => (
                    <div key={j} className="flex items-start gap-2 text-sm">
                      {task.status === 'completed' ? (
                        <CheckCircle size={14} className="text-green-500 mt-0.5" />
                      ) : (
                        <Circle size={14} className="text-zinc-500 mt-0.5" />
                      )}
                      <span className={cn(
                        task.status === 'completed' ? 'text-zinc-500 line-through' : 'text-zinc-300'
                      )}>
                        <span className="text-zinc-500">{task.id}:</span> {task.description}
                      </span>
                    </div>
                  ))}
                </div>
              ) : null}
            </div>
          ))}
        </div>
      ) : null}

      {/* Acceptance Criteria */}
      {data.global_acceptance_criteria?.length ? renderSection('Acceptance Criteria',
        <ul className="space-y-2">
          {data.global_acceptance_criteria.map((ac, i) => (
            <li key={i} className="flex items-start gap-2 text-zinc-300">
              <Flag size={14} className="text-green-500 mt-0.5" />
              <span>{ac}</span>
            </li>
          ))}
        </ul>
      ) : null}

      {/* Risks */}
      {data.risks?.length ? renderSection('Risks & Mitigations',
        <ul className="space-y-2">
          {data.risks.map((risk, i) => (
            <li key={i} className="flex items-start gap-2 text-zinc-300">
              <AlertTriangle size={14} className="text-amber-500 mt-0.5" />
              <span>{risk}</span>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  )
}
