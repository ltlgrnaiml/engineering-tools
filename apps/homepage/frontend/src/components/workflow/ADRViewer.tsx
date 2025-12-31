import { cn } from '@/lib/utils'
import { Calendar, Users, Tag, AlertTriangle, CheckCircle, Link as LinkIcon } from 'lucide-react'

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

interface AlternativeConsidered {
  name: string
  pros: string
  cons: string
  rejected_reason: string
}

interface Guardrail {
  id: string
  rule: string
  enforcement: string
  scope: string
}

interface ADRData {
  id?: string
  title?: string
  status?: string
  date?: string
  review_date?: string
  deciders?: string
  scope?: string
  context?: string
  decision_primary?: string
  decision_details?: {
    approach?: string
    constraints?: string[]
    implementation_specs?: string[]
  }
  consequences?: string[]
  alternatives_considered?: AlternativeConsidered[]
  tradeoffs?: string
  guardrails?: Guardrail[]
  cross_cutting_guardrails?: string[]
  references?: string[]
  tags?: string[]
  affected_components?: string[]
  resulting_specs?: Array<{ id: string; title?: string }>
  [key: string]: unknown
}

interface ADRViewerProps {
  content: string
  className?: string
}

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-zinc-600',
  proposed: 'bg-amber-600',
  active: 'bg-green-600',
  deprecated: 'bg-red-600',
  superseded: 'bg-purple-600',
}

export function ADRViewer({ content, className }: ADRViewerProps) {
  let data: ADRData = {}
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
          {data.scope && <Badge variant="outline">{data.scope}</Badge>}
        </div>
        <h1 className="text-2xl font-bold text-white mb-3">{data.title}</h1>
        <div className="flex flex-wrap gap-4 text-sm text-zinc-400">
          {data.date && (
            <span className="flex items-center gap-1">
              <Calendar size={14} /> {data.date}
            </span>
          )}
          {data.deciders && (
            <span className="flex items-center gap-1">
              <Users size={14} /> {data.deciders}
            </span>
          )}
        </div>
      </header>

      {/* Context */}
      {data.context && renderSection('Context', 
        <p className="text-zinc-300 whitespace-pre-wrap">{data.context}</p>
      )}

      {/* Decision */}
      {data.decision_primary && renderSection('Decision',
        <div className="bg-blue-900/20 border border-blue-700/50 rounded-lg p-4">
          <p className="text-blue-200 font-medium">{data.decision_primary}</p>
          {data.decision_details?.approach && (
            <div className="mt-3 text-zinc-300">
              <strong className="text-zinc-400">Approach:</strong>
              <p className="mt-1">{data.decision_details.approach}</p>
            </div>
          )}
        </div>
      )}

      {/* Constraints */}
      {data.decision_details?.constraints?.length ? renderSection('Constraints',
        renderList(data.decision_details.constraints, <AlertTriangle size={14} className="text-amber-500 mt-0.5" />)
      ) : null}

      {/* Implementation Specs */}
      {data.decision_details?.implementation_specs?.length ? renderSection('Implementation Specifications',
        renderList(data.decision_details.implementation_specs, <CheckCircle size={14} className="text-green-500 mt-0.5" />)
      ) : null}

      {/* Consequences */}
      {data.consequences?.length ? renderSection('Consequences', renderList(data.consequences)) : null}

      {/* Alternatives Considered */}
      {data.alternatives_considered?.length ? renderSection('Alternatives Considered',
        <div className="space-y-3">
          {data.alternatives_considered.map((alt, i) => (
            <div key={i} className="bg-zinc-800/50 rounded-lg p-3 border border-zinc-700">
              <h4 className="font-medium text-zinc-200 mb-2">{alt.name}</h4>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="text-green-400">Pros:</span>
                  <p className="text-zinc-300 mt-1">{alt.pros}</p>
                </div>
                <div>
                  <span className="text-red-400">Cons:</span>
                  <p className="text-zinc-300 mt-1">{alt.cons}</p>
                </div>
              </div>
              <div className="mt-2 text-sm">
                <span className="text-amber-400">Rejected:</span>
                <p className="text-zinc-400 mt-1">{alt.rejected_reason}</p>
              </div>
            </div>
          ))}
        </div>
      ) : null}

      {/* Tradeoffs */}
      {data.tradeoffs && renderSection('Tradeoffs',
        <p className="text-zinc-300 whitespace-pre-wrap">{data.tradeoffs}</p>
      )}

      {/* Guardrails */}
      {(data.guardrails?.length || data.cross_cutting_guardrails?.length) ? renderSection('Guardrails',
        <div className="space-y-3">
          {data.guardrails?.length ? (
            <div>
              <h4 className="text-sm font-medium text-zinc-400 mb-2">Specific</h4>
              <div className="space-y-2">
                {data.guardrails.map((g, i) => (
                  <div key={i} className="bg-zinc-800/50 rounded p-2 border border-zinc-700 text-sm">
                    <div className="flex items-center gap-2 mb-1">
                      <AlertTriangle size={14} className="text-amber-500" />
                      <span className="font-medium text-zinc-200">{g.rule}</span>
                    </div>
                    <div className="ml-5 text-zinc-400">
                      <span className="text-zinc-500">Enforcement:</span> {g.enforcement}
                    </div>
                    <div className="ml-5 text-zinc-400">
                      <span className="text-zinc-500">Scope:</span> {g.scope}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
          {data.cross_cutting_guardrails?.length ? (
            <div>
              <h4 className="text-sm font-medium text-zinc-400 mb-1">Cross-Cutting</h4>
              {renderList(data.cross_cutting_guardrails)}
            </div>
          ) : null}
        </div>
      ) : null}

      {/* References & Related */}
      {(data.references?.length || data.resulting_specs?.length) ? renderSection('References',
        <div className="space-y-3">
          {data.references?.length ? (
            <div>
              {renderList(data.references, <LinkIcon size={14} className="text-blue-400 mt-0.5" />)}
            </div>
          ) : null}
          {data.resulting_specs?.length ? (
            <div>
              <h4 className="text-sm font-medium text-zinc-400 mb-1">Resulting Specifications</h4>
              <ul className="space-y-1">
                {data.resulting_specs.map((spec, i) => (
                  <li key={i} className="text-blue-400">{spec.id}{spec.title ? `: ${spec.title}` : ''}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}

      {/* Tags */}
      {data.tags?.length ? renderSection('Tags',
        <div className="flex flex-wrap gap-2">
          {data.tags.map((tag, i) => (
            <Badge key={i} variant="outline" className="flex items-center gap-1">
              <Tag size={12} /> {tag}
            </Badge>
          ))}
        </div>
      ) : null}

      {/* Affected Components */}
      {data.affected_components?.length ? renderSection('Affected Components',
        <div className="flex flex-wrap gap-2">
          {data.affected_components.map((comp, i) => (
            <Badge key={i} variant="secondary">{comp}</Badge>
          ))}
        </div>
      ) : null}
    </div>
  )
}
