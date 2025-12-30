import { useState, useEffect } from 'react'
import { cn } from '@/lib/utils'

interface EditorFormProps {
  content: string
  onChange: (content: string) => void
  className?: string
}

export function EditorForm({ content, onChange, className }: EditorFormProps) {
  const [data, setData] = useState<Record<string, unknown>>({})

  useEffect(() => {
    try {
      setData(JSON.parse(content))
    } catch {
      setData({})
    }
  }, [content])

  const handleFieldChange = (field: string, value: unknown) => {
    const updated = { ...data, [field]: value }
    setData(updated)
    onChange(JSON.stringify(updated, null, 2))
  }

  const inputClass = 'w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded focus:outline-none focus:border-blue-500'

  return (
    <div className={cn('p-4 space-y-4 overflow-auto h-full', className)}>
      {/* Common fields */}
      <div>
        <label htmlFor="artifact-id" className="block text-sm text-zinc-400 mb-1">ID</label>
        <input
          id="artifact-id"
          type="text"
          value={String(data.id || '')}
          onChange={(e) => handleFieldChange('id', e.target.value)}
          className={inputClass}
          aria-label="Artifact ID"
        />
      </div>
      <div>
        <label htmlFor="artifact-title" className="block text-sm text-zinc-400 mb-1">Title</label>
        <input
          id="artifact-title"
          type="text"
          value={String(data.title || '')}
          onChange={(e) => handleFieldChange('title', e.target.value)}
          className={inputClass}
          aria-label="Artifact title"
        />
      </div>
      <div>
        <label htmlFor="artifact-status" className="block text-sm text-zinc-400 mb-1">Status</label>
        <select
          id="artifact-status"
          value={String(data.status || 'draft')}
          onChange={(e) => handleFieldChange('status', e.target.value)}
          className={inputClass}
          aria-label="Artifact status"
        >
          <option value="draft">Draft</option>
          <option value="proposed">Proposed</option>
          <option value="active">Active</option>
          <option value="deprecated">Deprecated</option>
          <option value="superseded">Superseded</option>
        </select>
      </div>
      <div>
        <label htmlFor="artifact-context" className="block text-sm text-zinc-400 mb-1">Context</label>
        <textarea
          id="artifact-context"
          value={String(data.context || '')}
          onChange={(e) => handleFieldChange('context', e.target.value)}
          rows={4}
          className={inputClass}
          aria-label="Artifact context"
        />
      </div>
      <div>
        <label htmlFor="artifact-decision" className="block text-sm text-zinc-400 mb-1">Decision</label>
        <textarea
          id="artifact-decision"
          value={String(data.decision_primary || data.decision || '')}
          onChange={(e) => handleFieldChange('decision_primary', e.target.value)}
          rows={4}
          className={inputClass}
          aria-label="Artifact decision"
        />
      </div>
    </div>
  )
}
