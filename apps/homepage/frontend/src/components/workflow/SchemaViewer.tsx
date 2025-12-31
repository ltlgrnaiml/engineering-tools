import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'

interface SchemaViewerProps {
  data: unknown
  className?: string
}

/**
 * Generic schema-aware viewer that renders any JSON structure dynamically.
 * No hardcoded interfaces - adapts to any Pydantic schema automatically.
 */
export function SchemaViewer({ data, className }: SchemaViewerProps) {
  if (!data || typeof data !== 'object') {
    return <div className="p-4 text-zinc-400">No data to display</div>
  }

  const obj = data as Record<string, unknown>
  
  // Extract header fields if present
  const id = obj.id as string | undefined
  const title = obj.title as string | undefined
  const status = obj.status as string | undefined
  const version = obj.version as string | undefined
  const schemaType = obj.schema_type as string | undefined

  // Fields to show in header (exclude from body)
  const headerFields = ['id', 'title', 'status', 'version', 'schema_type']
  const bodyEntries = Object.entries(obj).filter(([key]) => !headerFields.includes(key))

  return (
    <div className={cn('p-6 overflow-auto h-full', className)}>
      {/* Header */}
      {(id || title || status) && (
        <header className="mb-6 pb-4 border-b border-zinc-700">
          <div className="flex items-center gap-2 flex-wrap mb-2">
            {id && <span className="text-sm font-mono text-zinc-500">{id}</span>}
            {status && <StatusBadge status={status} />}
            {version && <Badge variant="outline">v{version}</Badge>}
            {schemaType && <Badge variant="secondary">{schemaType}</Badge>}
          </div>
          {title && <h1 className="text-2xl font-bold text-white">{title}</h1>}
        </header>
      )}

      {/* Body - render all other fields */}
      <div className="space-y-6">
        {bodyEntries.map(([key, value]) => (
          <FieldRenderer key={key} fieldName={key} value={value} level={0} />
        ))}
      </div>
    </div>
  )
}

// Render a single field with smart formatting based on type
function FieldRenderer({ fieldName, value, level }: { fieldName: string; value: unknown; level: number }) {
  const label = formatFieldName(fieldName)
  
  // Null/undefined
  if (value === null || value === undefined) {
    return null // Don't render empty fields
  }

  // Primitives
  if (typeof value === 'string') {
    // Long strings get their own section
    if (value.length > 100) {
      return (
        <Section title={label}>
          <p className="text-zinc-300 whitespace-pre-wrap">{value}</p>
        </Section>
      )
    }
    // Short strings inline
    return (
      <div className="flex gap-2">
        <span className="text-zinc-500 min-w-32">{label}:</span>
        <span className="text-zinc-300">{value}</span>
      </div>
    )
  }

  if (typeof value === 'number' || typeof value === 'boolean') {
    return (
      <div className="flex gap-2">
        <span className="text-zinc-500 min-w-32">{label}:</span>
        <span className="text-blue-300">{String(value)}</span>
      </div>
    )
  }

  // Arrays
  if (Array.isArray(value)) {
    if (value.length === 0) return null
    
    // Array of strings - render as list
    if (value.every(item => typeof item === 'string')) {
      return (
        <Section title={label}>
          <ul className="list-disc list-inside space-y-1 text-zinc-300">
            {value.map((item, i) => <li key={i}>{item}</li>)}
          </ul>
        </Section>
      )
    }
    
    // Array of objects - render as cards
    return (
      <Section title={label}>
        <div className="space-y-3">
          {value.map((item, i) => (
            <ObjectCard key={i} data={item} level={level + 1} />
          ))}
        </div>
      </Section>
    )
  }

  // Objects
  if (typeof value === 'object') {
    return (
      <Section title={label}>
        <ObjectCard data={value} level={level + 1} />
      </Section>
    )
  }

  return null
}

// Render an object as a card
function ObjectCard({ data, level }: { data: unknown; level: number }) {
  const [expanded, setExpanded] = useState(level < 2)
  
  if (!data || typeof data !== 'object') {
    return <span className="text-zinc-400">{String(data)}</span>
  }

  const obj = data as Record<string, unknown>
  const entries = Object.entries(obj)
  
  // Try to find a "title" or "name" or "id" field for the card header
  const titleField = obj.title || obj.name || obj.id || obj.description
  const titleStr = typeof titleField === 'string' ? titleField : null
  
  // Get remaining fields
  const headerKeys = ['title', 'name', 'id']
  const bodyEntries = entries.filter(([key]) => !headerKeys.includes(key) || !titleStr)

  return (
    <div className="bg-zinc-800/50 rounded-lg border border-zinc-700 overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-2 p-3 text-left hover:bg-zinc-800/80"
      >
        {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        {titleStr ? (
          <span className="font-medium text-zinc-200">{titleStr}</span>
        ) : (
          <span className="text-zinc-400">{entries.length} fields</span>
        )}
        {typeof obj.status === 'string' && <StatusBadge status={obj.status} size="sm" />}
        {typeof obj.id === 'string' && !titleStr && <span className="text-xs text-zinc-500 ml-auto">{obj.id}</span>}
      </button>
      
      {expanded && bodyEntries.length > 0 && (
        <div className="p-3 pt-0 space-y-2 border-t border-zinc-700/50">
          {bodyEntries.map(([key, value]) => (
            <NestedField key={key} fieldName={key} value={value} level={level} />
          ))}
        </div>
      )}
    </div>
  )
}

// Render nested field inside a card (more compact)
function NestedField({ fieldName, value, level }: { fieldName: string; value: unknown; level: number }) {
  const label = formatFieldName(fieldName)

  if (value === null || value === undefined) return null

  // Primitives
  if (typeof value === 'string') {
    if (value.length > 200) {
      return (
        <div>
          <span className="text-sm text-zinc-500">{label}</span>
          <p className="text-zinc-300 text-sm mt-1 whitespace-pre-wrap">{value}</p>
        </div>
      )
    }
    return (
      <div className="flex gap-2 text-sm">
        <span className="text-zinc-500">{label}:</span>
        <span className="text-zinc-300">{value}</span>
      </div>
    )
  }

  if (typeof value === 'number' || typeof value === 'boolean') {
    return (
      <div className="flex gap-2 text-sm">
        <span className="text-zinc-500">{label}:</span>
        <span className="text-blue-300">{String(value)}</span>
      </div>
    )
  }

  // Arrays
  if (Array.isArray(value)) {
    if (value.length === 0) return null
    
    if (value.every(item => typeof item === 'string')) {
      return (
        <div>
          <span className="text-sm text-zinc-500">{label}</span>
          <ul className="list-disc list-inside text-sm text-zinc-300 mt-1">
            {value.map((item, i) => <li key={i}>{item}</li>)}
          </ul>
        </div>
      )
    }
    
    // Nested objects in array - recurse
    return (
      <div>
        <span className="text-sm text-zinc-500">{label}</span>
        <div className="mt-1 space-y-2">
          {value.map((item, i) => (
            <ObjectCard key={i} data={item} level={level + 1} />
          ))}
        </div>
      </div>
    )
  }

  // Nested objects
  if (typeof value === 'object') {
    return (
      <div>
        <span className="text-sm text-zinc-500">{label}</span>
        <div className="mt-1">
          <ObjectCard data={value} level={level + 1} />
        </div>
      </div>
    )
  }

  return null
}

// Section with title
function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h3 className="text-lg font-semibold text-zinc-200 mb-2 border-b border-zinc-700 pb-1">
        {title}
      </h3>
      {children}
    </section>
  )
}

// Status badge with colors
function StatusBadge({ status, size = 'default' }: { status: string; size?: 'default' | 'sm' }) {
  const colors: Record<string, string> = {
    draft: 'bg-zinc-600',
    proposed: 'bg-amber-600',
    active: 'bg-green-600',
    accepted: 'bg-green-600',
    deprecated: 'bg-red-600',
    superseded: 'bg-purple-600',
    completed: 'bg-blue-600',
    pending: 'bg-zinc-600',
    in_progress: 'bg-blue-600',
  }
  const color = colors[status.toLowerCase()] || 'bg-zinc-600'
  const sizeClass = size === 'sm' ? 'text-xs px-1.5 py-0.5' : 'text-xs px-2 py-0.5'
  
  return (
    <span className={cn('inline-flex items-center rounded font-medium text-white', color, sizeClass)}>
      {status}
    </span>
  )
}

// Generic badge
function Badge({ children, variant = 'default', className }: { 
  children: React.ReactNode
  variant?: 'default' | 'outline' | 'secondary'
  className?: string 
}) {
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

// Convert field_name to "Field Name"
function formatFieldName(name: string): string {
  return name
    .replace(/_/g, ' ')
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, str => str.toUpperCase())
    .trim()
}
