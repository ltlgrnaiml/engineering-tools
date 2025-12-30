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
        <label className="block text-sm text-zinc-400 mb-1">ID</label>
        <input
          type="text"
          value={String(data.id || '')}
          onChange={(e) => handleFieldChange('id', e.target.value)}
          className={inputClass}
        />
      </div>
      <div>
        <label className="block text-sm text-zinc-400 mb-1">Title</label>
        <input
          type="text"
          value={String(data.title || '')}
          onChange={(e) => handleFieldChange('title', e.target.value)}
          className={inputClass}
        />
      </div>
      <div>
        <label className="block text-sm text-zinc-400 mb-1">Status</label>
        <select
          value={String(data.status || 'draft')}
          onChange={(e) => handleFieldChange('status', e.target.value)}
          className={inputClass}
        >
          <option value="draft">Draft</option>
          <option value="proposed">Proposed</option>
          <option value="active">Active</option>
          <option value="deprecated">Deprecated</option>
          <option value="superseded">Superseded</option>
        </select>
      </div>
      <div>
        <label className="block text-sm text-zinc-400 mb-1">Context</label>
        <textarea
          value={String(data.context || '')}
          onChange={(e) => handleFieldChange('context', e.target.value)}
          rows={4}
          className={inputClass}
        />
      </div>
      <div>
        <label className="block text-sm text-zinc-400 mb-1">Decision</label>
        <textarea
          value={String(data.decision_primary || data.decision || '')}
          onChange={(e) => handleFieldChange('decision_primary', e.target.value)}
          rows={4}
          className={inputClass}
        />
      </div>
    </div>
  )
}
