import { cn } from '@/lib/utils'
import { FileText, CheckCircle, AlertTriangle, Link as LinkIcon, TestTube } from 'lucide-react'

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

interface FunctionalRequirement {
  id: string
  category?: string
  description: string
  acceptance_criteria?: string[]
  api_endpoint?: {
    method: string
    path: string
    query_params?: string[]
    response_model?: string
  }
}

interface SpecData {
  id?: string
  title?: string
  status?: string
  version?: string
  scope?: string
  implements_adr?: string[]
  source_discussion?: string
  overview?: string | {
    purpose?: string
    scope?: string
    out_of_scope?: string[]
  }
  requirements?: string[] | {
    functional?: FunctionalRequirement[]
    non_functional?: string[]
  }
  behaviors?: Array<{ id: string; description: string; acceptance_criteria: string }>
  constraints?: string[]
  interfaces?: string[]
  testing_requirements?: string[]
  tier_0_contracts?: Array<{ module: string; classes: string[] }>
  [key: string]: unknown
}

interface SpecViewerProps {
  content: string
  className?: string
}

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-zinc-600',
  review: 'bg-amber-600',
  active: 'bg-green-600',
  deprecated: 'bg-red-600',
}

export function SpecViewer({ content, className }: SpecViewerProps) {
  let data: SpecData = {}
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

  const renderList = (items: string[] | undefined, icon?: React.ReactNode) => {
    if (!items?.length) return <p className="text-zinc-500 italic">None specified</p>
    return (
      <ul className="space-y-1">
        {items.map((item, i) => (
          <li key={i} className="flex items-start gap-2 text-zinc-300">
            {icon || <span className="text-zinc-500">•</span>}
            <span>{item}</span>
          </li>
        ))}
      </ul>
    )
  }

  return (
    <div className={cn('p-6 overflow-auto h-full', className)}>
      {/* Header */}
      <header className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <span className="text-sm font-mono text-zinc-500">{data.id}</span>
          <Badge className={cn('text-white', STATUS_COLORS[data.status || 'draft'])}>
            {data.status || 'draft'}
          </Badge>
          {data.version && <Badge variant="outline">v{data.version}</Badge>}
          {data.scope && <Badge variant="secondary">{data.scope}</Badge>}
        </div>
        <h1 className="text-2xl font-bold text-white mb-3">{data.title}</h1>
      </header>

      {/* Implements ADRs */}
      {data.implements_adr?.length ? renderSection('Implements ADRs',
        <div className="flex flex-wrap gap-2">
          {data.implements_adr.map((adr, i) => (
            <Badge key={i} variant="outline" className="flex items-center gap-1">
              <LinkIcon size={12} /> {adr}
            </Badge>
          ))}
        </div>
      ) : null}

      {/* Overview */}
      {data.overview && renderSection('Overview',
        typeof data.overview === 'string' ? (
          <p className="text-zinc-300 whitespace-pre-wrap">{data.overview}</p>
        ) : (
          <div className="space-y-3">
            {data.overview.purpose && (
              <div>
                <h4 className="text-sm font-medium text-zinc-400 mb-1">Purpose</h4>
                <p className="text-zinc-300">{data.overview.purpose}</p>
              </div>
            )}
            {data.overview.scope && (
              <div>
                <h4 className="text-sm font-medium text-zinc-400 mb-1">Scope</h4>
                <p className="text-zinc-300">{data.overview.scope}</p>
              </div>
            )}
            {data.overview.out_of_scope?.length ? (
              <div>
                <h4 className="text-sm font-medium text-zinc-400 mb-1">Out of Scope</h4>
                <ul className="list-disc list-inside text-zinc-400">
                  {data.overview.out_of_scope.map((item, i) => <li key={i}>{item}</li>)}
                </ul>
              </div>
            ) : null}
          </div>
        )
      )}

      {/* Requirements */}
      {data.requirements && renderSection('Requirements',
        Array.isArray(data.requirements) ? (
          renderList(data.requirements, <CheckCircle size={14} className="text-green-500 mt-0.5" />)
        ) : (
          <div className="space-y-4">
            {data.requirements.functional?.map((req, i) => (
              <div key={i} className="bg-zinc-800/50 rounded-lg p-4 border border-zinc-700">
                <div className="flex items-center gap-2 mb-2">
                  <Badge variant="outline">{req.id}</Badge>
                  {req.category && <Badge variant="secondary">{req.category}</Badge>}
                </div>
                <p className="text-zinc-300 mb-2">{req.description}</p>
                {req.acceptance_criteria?.length ? (
                  <div className="mt-2">
                    <h4 className="text-sm font-medium text-zinc-400 mb-1">Acceptance Criteria</h4>
                    <ul className="list-disc list-inside text-sm text-green-300 space-y-1">
                      {req.acceptance_criteria.map((ac, j) => <li key={j}>{ac}</li>)}
                    </ul>
                  </div>
                ) : null}
                {req.api_endpoint && (
                  <div className="mt-2 text-sm">
                    <span className="text-zinc-500">API: </span>
                    <code className="bg-zinc-900 px-2 py-0.5 rounded text-blue-300">
                      {req.api_endpoint.method} {req.api_endpoint.path}
                    </code>
                  </div>
                )}
              </div>
            ))}
          </div>
        )
      )}

      {/* Behaviors */}
      {data.behaviors?.length ? renderSection('Behaviors',
        <div className="space-y-4">
          {data.behaviors.map((behavior, i) => (
            <div key={i} className="bg-zinc-800/50 rounded-lg p-4 border border-zinc-700">
              <div className="flex items-center gap-2 mb-2">
                <Badge variant="outline">{behavior.id}</Badge>
              </div>
              <p className="text-zinc-300 mb-2">{behavior.description}</p>
              {behavior.acceptance_criteria && (
                <div className="mt-2 text-sm">
                  <span className="text-zinc-500">Acceptance Criteria:</span>
                  <p className="text-green-300 mt-1">{behavior.acceptance_criteria}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      ) : null}

      {/* Constraints */}
      {data.constraints?.length ? renderSection('Constraints',
        renderList(data.constraints, <AlertTriangle size={14} className="text-amber-500 mt-0.5" />)
      ) : null}

      {/* Interfaces */}
      {data.interfaces?.length ? renderSection('Interfaces',
        renderList(data.interfaces, <FileText size={14} className="text-blue-400 mt-0.5" />)
      ) : null}

      {/* Testing Requirements */}
      {data.testing_requirements?.length ? renderSection('Testing Requirements',
        renderList(data.testing_requirements, <TestTube size={14} className="text-purple-400 mt-0.5" />)
      ) : null}
    </div>
  )
}
