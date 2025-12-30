import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'

interface JsonRendererProps {
  data: object
  className?: string
}

export function JsonRenderer({ data, className }: JsonRendererProps) {
  return (
    <div className={cn('font-mono text-sm', className)}>
      <JsonNode data={data} level={0} />
    </div>
  )
}

function JsonNode({ data, level }: { data: unknown; level: number }) {
  const [expanded, setExpanded] = useState(level < 2)
  const indentClass = level === 0 ? 'ml-0' : level === 1 ? 'ml-4' : level === 2 ? 'ml-8' : 'ml-12'

  if (data === null) return <span className="text-zinc-500">null</span>
  if (typeof data === 'boolean') return <span className="text-amber-400">{String(data)}</span>
  if (typeof data === 'number') return <span className="text-blue-400">{data}</span>
  if (typeof data === 'string') return <span className="text-green-400">"{data}"</span>

  if (Array.isArray(data)) {
    if (data.length === 0) return <span className="text-zinc-500">[]</span>
    return (
      <div>
        <button 
          onClick={() => setExpanded(!expanded)} 
          className="inline-flex items-center hover:text-blue-400"
          aria-label={expanded ? 'Collapse array' : 'Expand array'}
          aria-expanded={expanded}
        >
          {expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
          <span className="text-zinc-500">[{data.length}]</span>
        </button>
        {expanded && (
          <div className={indentClass}>
            {data.map((item, i) => (
              <div key={i}><JsonNode data={item} level={level + 1} /></div>
            ))}
          </div>
        )}
      </div>
    )
  }

  if (typeof data === 'object') {
    const entries = Object.entries(data)
    if (entries.length === 0) return <span className="text-zinc-500">{'{}'}</span>
    return (
      <div>
        <button 
          onClick={() => setExpanded(!expanded)} 
          className="inline-flex items-center hover:text-blue-400"
          aria-label={expanded ? 'Collapse object' : 'Expand object'}
          aria-expanded={expanded}
        >
          {expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
          <span className="text-zinc-500">{'{...}'}</span>
        </button>
        {expanded && (
          <div className={indentClass}>
            {entries.map(([key, value]) => (
              <div key={key} className="flex">
                <span className="text-purple-400">{key}</span>
                <span className="text-zinc-500 mx-1">:</span>
                <JsonNode data={value} level={level + 1} />
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  return <span>{String(data)}</span>
}
