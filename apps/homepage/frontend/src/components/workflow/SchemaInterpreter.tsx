import { useState, useEffect } from 'react'
import { ChevronDown, ChevronRight, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

const API_BASE = 'http://localhost:8000/api/devtools'

// JSON Schema type definitions
interface JSONSchemaProperty {
  type?: string | string[]
  title?: string
  description?: string
  enum?: string[]
  items?: JSONSchemaProperty
  properties?: Record<string, JSONSchemaProperty>
  $ref?: string
  anyOf?: JSONSchemaProperty[]
  allOf?: JSONSchemaProperty[]
  default?: unknown
  format?: string
}

interface JSONSchema {
  type?: string
  title?: string
  description?: string
  properties?: Record<string, JSONSchemaProperty>
  required?: string[]
  $defs?: Record<string, JSONSchemaProperty>
  $schema_type?: string
}

interface SchemaInterpreterProps {
  schemaType: 'adr' | 'spec' | 'plan'
  data: Record<string, unknown>
  className?: string
}

/**
 * Schema-driven viewer that renders UI dynamically from JSON Schema.
 * 
 * This component:
 * 1. Fetches the JSON Schema for the artifact type from the backend
 * 2. Uses schema properties to render appropriate UI elements
 * 3. Handles nested objects, arrays, and $ref definitions
 * 4. Displays field descriptions and constraints from the schema
 */
export function SchemaInterpreter({ schemaType, data, className }: SchemaInterpreterProps) {
  const [schema, setSchema] = useState<JSONSchema | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch schema on mount or when schemaType changes
  useEffect(() => {
    const fetchSchema = async () => {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch(`${API_BASE}/schemas/${schemaType}`)
        if (!res.ok) throw new Error(`Failed to fetch schema: ${res.status}`)
        const schemaData = await res.json()
        setSchema(schemaData)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error fetching schema')
      } finally {
        setLoading(false)
      }
    }
    fetchSchema()
  }, [schemaType])

  // Extract header fields
  const headerFields = ['id', 'title', 'status', 'version', 'schema_type']
  const id = data.id as string | undefined
  const title = data.title as string | undefined
  const status = data.status as string | undefined
  const version = data.version as string | undefined

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-zinc-500" />
        <span className="ml-2 text-zinc-500">Loading schema...</span>
      </div>
    )
  }

  if (error) {
    return <div className="p-4 text-red-400">Error: {error}</div>
  }

  if (!schema) {
    return <div className="p-4 text-zinc-500">No schema available</div>
  }

  return (
    <div className={cn('p-6 overflow-auto h-full', className)}>
      {/* Header */}
      {(id || title || status) && (
        <header className="mb-6 pb-4 border-b border-zinc-700">
          <div className="flex items-center gap-2 flex-wrap mb-2">
            {id && <span className="text-sm font-mono text-zinc-500">{id}</span>}
            {status && <StatusBadge status={status} />}
            {version && <Badge variant="outline">v{version}</Badge>}
          </div>
          {title && <h1 className="text-2xl font-bold text-white">{title}</h1>}
          {schema.description && (
            <p className="text-sm text-zinc-500 mt-1">{schema.description}</p>
          )}
        </header>
      )}

      {/* Render schema-driven fields */}
      <div className="space-y-6">
        {schema.properties && Object.entries(schema.properties)
          .filter(([key]) => !headerFields.includes(key))
          .map(([key, prop]) => (
            <SchemaField
              key={key}
              fieldName={key}
              property={prop}
              value={data[key]}
              schema={schema}
              level={0}
            />
          ))
        }
      </div>
    </div>
  )
}

// Render a single field based on its schema definition
interface SchemaFieldProps {
  fieldName: string
  property: JSONSchemaProperty
  value: unknown
  schema: JSONSchema
  level: number
}

function SchemaField({ fieldName, property, value, schema, level }: SchemaFieldProps) {
  // Skip null/undefined values
  if (value === null || value === undefined) return null

  // Resolve $ref if present
  const resolvedProp = property.$ref 
    ? resolveRef(property.$ref, schema) 
    : property

  // Get display label from schema title or format field name
  const label = resolvedProp.title || formatFieldName(fieldName)
  const description = resolvedProp.description

  // Determine the type (handle anyOf, arrays, etc.)
  const propType = getPropertyType(resolvedProp)

  // Render based on type
  if (propType === 'string' && typeof value === 'string') {
    // Long strings get their own section
    if (value.length > 100) {
      return (
        <Section title={label} description={description}>
          <p className="text-zinc-300 whitespace-pre-wrap">{value}</p>
        </Section>
      )
    }
    // Enum values get badges
    if (resolvedProp.enum) {
      return (
        <div className="flex gap-2 items-center">
          <span className="text-zinc-500 min-w-32">{label}:</span>
          <Badge variant="outline">{value}</Badge>
        </div>
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

  if ((propType === 'integer' || propType === 'number' || propType === 'boolean') && 
      (typeof value === 'number' || typeof value === 'boolean')) {
    return (
      <div className="flex gap-2">
        <span className="text-zinc-500 min-w-32">{label}:</span>
        <span className="text-blue-300">{String(value)}</span>
      </div>
    )
  }

  if (propType === 'array' && Array.isArray(value)) {
    if (value.length === 0) return null
    
    const itemSchema = resolvedProp.items
    
    // Array of strings - render as list
    if (value.every(item => typeof item === 'string')) {
      return (
        <Section title={label} description={description}>
          <ul className="list-disc list-inside space-y-1 text-zinc-300">
            {value.map((item, i) => <li key={i}>{item as string}</li>)}
          </ul>
        </Section>
      )
    }
    
    // Array of objects - render as collapsible cards
    return (
      <Section title={label} description={description}>
        <div className="space-y-2">
          {value.map((item, i) => (
            <ObjectCard 
              key={i} 
              data={item as Record<string, unknown>} 
              itemSchema={itemSchema}
              schema={schema}
              level={level + 1} 
            />
          ))}
        </div>
      </Section>
    )
  }

  if (propType === 'object' && typeof value === 'object' && value !== null) {
    return (
      <Section title={label} description={description}>
        <ObjectCard 
          data={value as Record<string, unknown>}
          itemSchema={resolvedProp}
          schema={schema}
          level={level + 1}
        />
      </Section>
    )
  }

  // Fallback for unknown types
  return (
    <div className="flex gap-2">
      <span className="text-zinc-500 min-w-32">{label}:</span>
      <span className="text-zinc-400">{JSON.stringify(value)}</span>
    </div>
  )
}

// Render an object as a collapsible card
interface ObjectCardProps {
  data: Record<string, unknown>
  itemSchema?: JSONSchemaProperty
  schema: JSONSchema
  level: number
}

function ObjectCard({ data, itemSchema, schema, level }: ObjectCardProps) {
  const [expanded, setExpanded] = useState(level < 2)
  
  // Try to find a title field for the card header
  const titleValue = data.title || data.name || data.id || data.description
  const titleStr = typeof titleValue === 'string' ? titleValue : null
  const statusValue = data.status
  
  // Get properties from itemSchema or data keys
  const properties = itemSchema?.properties || {}
  const dataKeys = Object.keys(data)

  return (
    <div className="bg-zinc-800/50 rounded-lg border border-zinc-700 overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-2 p-3 text-left hover:bg-zinc-800/80"
      >
        {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        {titleStr ? (
          <span className="font-medium text-zinc-200 truncate">{titleStr}</span>
        ) : (
          <span className="text-zinc-400">{dataKeys.length} fields</span>
        )}
        {typeof statusValue === 'string' && <StatusBadge status={statusValue} size="sm" />}
      </button>
      
      {expanded && (
        <div className="p-3 pt-0 space-y-2 border-t border-zinc-700/50">
          {dataKeys.map(key => {
            const prop = properties[key] || { type: 'string' }
            const value = data[key]
            if (value === null || value === undefined) return null
            if (['title', 'name', 'id'].includes(key) && titleStr) return null // Skip header field
            
            return (
              <NestedField
                key={key}
                fieldName={key}
                property={prop}
                value={value}
                schema={schema}
                level={level}
              />
            )
          })}
        </div>
      )}
    </div>
  )
}

// Compact field rendering for nested objects
function NestedField({ fieldName, property, value, schema, level }: SchemaFieldProps) {
  const resolvedProp = property.$ref ? resolveRef(property.$ref, schema) : property
  const label = resolvedProp.title || formatFieldName(fieldName)

  if (value === null || value === undefined) return null

  // Strings
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

  // Numbers/booleans
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
            {value.map((item, i) => <li key={i}>{item as string}</li>)}
          </ul>
        </div>
      )
    }
    return (
      <div>
        <span className="text-sm text-zinc-500">{label}</span>
        <div className="mt-1 space-y-2">
          {value.map((item, i) => (
            <ObjectCard 
              key={i} 
              data={item as Record<string, unknown>}
              itemSchema={resolvedProp.items}
              schema={schema}
              level={level + 1}
            />
          ))}
        </div>
      </div>
    )
  }

  // Nested objects
  if (typeof value === 'object' && value !== null) {
    return (
      <div>
        <span className="text-sm text-zinc-500">{label}</span>
        <div className="mt-1">
          <ObjectCard 
            data={value as Record<string, unknown>}
            itemSchema={resolvedProp}
            schema={schema}
            level={level + 1}
          />
        </div>
      </div>
    )
  }

  return null
}

// Helper: Resolve $ref to actual definition
function resolveRef(ref: string, schema: JSONSchema): JSONSchemaProperty {
  // Handle "#/$defs/Name" format
  const match = ref.match(/^#\/\$defs\/(.+)$/)
  if (match && schema.$defs) {
    return schema.$defs[match[1]] || { type: 'string' }
  }
  return { type: 'string' }
}

// Helper: Get the primary type from a property (handling anyOf, etc.)
function getPropertyType(prop: JSONSchemaProperty): string {
  if (prop.type) {
    return Array.isArray(prop.type) ? prop.type[0] : prop.type
  }
  if (prop.anyOf) {
    // Find first non-null type
    const nonNull = prop.anyOf.find(p => p.type !== 'null')
    if (nonNull?.type) return Array.isArray(nonNull.type) ? nonNull.type[0] : nonNull.type
  }
  if (prop.allOf) {
    return 'object'
  }
  if (prop.enum) {
    return 'string'
  }
  return 'string'
}

// Helper: Format field_name to "Field Name"
function formatFieldName(name: string): string {
  return name
    .replace(/_/g, ' ')
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, str => str.toUpperCase())
    .trim()
}

// Section component
function Section({ title, description, children }: { 
  title: string
  description?: string
  children: React.ReactNode 
}) {
  return (
    <section>
      <h3 className="text-lg font-semibold text-zinc-200 mb-1 border-b border-zinc-700 pb-1">
        {title}
      </h3>
      {description && (
        <p className="text-xs text-zinc-500 mb-2">{description}</p>
      )}
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
    review: 'bg-amber-600',
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
