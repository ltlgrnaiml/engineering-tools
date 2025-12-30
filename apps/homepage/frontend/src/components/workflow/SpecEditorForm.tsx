import { useState, useEffect, useCallback } from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface SpecFormData {
  id?: string
  title?: string
  status?: string
  version?: string
  implements_adr?: string[]
  scope?: string
  overview?: string
  requirements?: string[]
  behaviors?: Array<{ id: string; description: string; acceptance_criteria: string }>
  constraints?: string[]
  interfaces?: string[]
  testing_requirements?: string[]
  [key: string]: unknown
}

interface SpecEditorFormProps {
  content: string
  onChange: (content: string) => void
  className?: string
}

const STATUS_OPTIONS = ['draft', 'review', 'active', 'deprecated']

export function SpecEditorForm({ content, onChange, className }: SpecEditorFormProps) {
  const [formData, setFormData] = useState<SpecFormData>({})

  useEffect(() => {
    try {
      setFormData(JSON.parse(content))
    } catch {
      setFormData({})
    }
  }, [content])

  const updateForm = useCallback((updates: Partial<SpecFormData>) => {
    const updated = { ...formData, ...updates }
    setFormData(updated)
    onChange(JSON.stringify(updated, null, 2))
  }, [formData, onChange])

  const handleFieldChange = (field: string, value: unknown) => {
    updateForm({ [field]: value })
  }

  const handleArrayChange = (field: string, index: number, value: string) => {
    const arr = [...((formData[field] as string[]) || [])]
    arr[index] = value
    updateForm({ [field]: arr })
  }

  const addArrayItem = (field: string) => {
    const arr = [...((formData[field] as string[]) || []), '']
    updateForm({ [field]: arr })
  }

  const removeArrayItem = (field: string, index: number) => {
    const arr = ((formData[field] as string[]) || []).filter((_, i) => i !== index)
    updateForm({ [field]: arr })
  }

  const addBehavior = () => {
    const behaviors = [...(formData.behaviors || []), { id: `BEH-${(formData.behaviors?.length || 0) + 1}`, description: '', acceptance_criteria: '' }]
    updateForm({ behaviors })
  }

  const updateBehavior = (index: number, updates: Partial<{ id: string; description: string; acceptance_criteria: string }>) => {
    const behaviors = [...(formData.behaviors || [])]
    behaviors[index] = { ...behaviors[index], ...updates }
    updateForm({ behaviors })
  }

  const removeBehavior = (index: number) => {
    const behaviors = (formData.behaviors || []).filter((_, i) => i !== index)
    updateForm({ behaviors })
  }

  const inputClass = 'w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded focus:outline-none focus:border-blue-500 text-sm'
  const labelClass = 'block text-sm text-zinc-400 mb-1'

  const renderArrayField = (label: string, field: string, placeholder = 'Add item...') => {
    const items = (formData[field] as string[]) || []
    return (
      <div>
        <label className={labelClass}>{label}</label>
        <div className="space-y-2">
          {items.map((item, i) => (
            <div key={i} className="flex gap-2">
              <input
                type="text"
                value={item}
                onChange={(e) => handleArrayChange(field, i, e.target.value)}
                placeholder={placeholder}
                className={cn(inputClass, 'flex-1')}
                aria-label={`${label} item ${i + 1}`}
              />
              <button
                type="button"
                onClick={() => removeArrayItem(field, i)}
                className="p-2 text-red-400 hover:bg-zinc-800 rounded"
                aria-label={`Remove ${label} item`}
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))}
          <button
            type="button"
            onClick={() => addArrayItem(field)}
            className="flex items-center gap-1 text-sm text-blue-400 hover:text-blue-300"
          >
            <Plus size={14} /> Add {label.toLowerCase()}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className={cn('p-4 space-y-6 overflow-auto h-full', className)}>
      {/* Identity Section */}
      <section>
        <h3 className="text-lg font-medium text-zinc-200 mb-3 border-b border-zinc-700 pb-2">Identity</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="spec-id" className={labelClass}>ID</label>
            <input
              id="spec-id"
              type="text"
              value={String(formData.id || '')}
              onChange={(e) => handleFieldChange('id', e.target.value)}
              className={inputClass}
              aria-label="Specification ID"
            />
          </div>
          <div>
            <label htmlFor="spec-version" className={labelClass}>Version</label>
            <input
              id="spec-version"
              type="text"
              value={String(formData.version || '')}
              onChange={(e) => handleFieldChange('version', e.target.value)}
              className={inputClass}
              placeholder="YYYY.MM.PATCH"
              aria-label="Version"
            />
          </div>
        </div>
        <div className="mt-4">
          <label htmlFor="spec-title" className={labelClass}>Title</label>
          <input
            id="spec-title"
            type="text"
            value={String(formData.title || '')}
            onChange={(e) => handleFieldChange('title', e.target.value)}
            className={inputClass}
            aria-label="Specification title"
          />
        </div>
        <div className="grid grid-cols-2 gap-4 mt-4">
          <div>
            <label htmlFor="spec-status" className={labelClass}>Status</label>
            <select
              id="spec-status"
              value={String(formData.status || 'draft')}
              onChange={(e) => handleFieldChange('status', e.target.value)}
              className={inputClass}
              aria-label="Specification status"
            >
              {STATUS_OPTIONS.map(opt => <option key={opt} value={opt}>{opt}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="spec-scope" className={labelClass}>Scope</label>
            <input
              id="spec-scope"
              type="text"
              value={String(formData.scope || '')}
              onChange={(e) => handleFieldChange('scope', e.target.value)}
              className={inputClass}
              placeholder="core, dat, pptx, sov"
              aria-label="Scope"
            />
          </div>
        </div>
      </section>

      {/* Implements ADR */}
      <section>
        <h3 className="text-lg font-medium text-zinc-200 mb-3 border-b border-zinc-700 pb-2">Implements ADRs</h3>
        {renderArrayField('ADR References', 'implements_adr', 'ADR-XXXX')}
      </section>

      {/* Overview */}
      <section>
        <h3 className="text-lg font-medium text-zinc-200 mb-3 border-b border-zinc-700 pb-2">Overview</h3>
        <textarea
          value={String(formData.overview || '')}
          onChange={(e) => handleFieldChange('overview', e.target.value)}
          rows={4}
          className={inputClass}
          placeholder="Brief overview of what this specification covers..."
          aria-label="Overview"
        />
      </section>

      {/* Requirements */}
      <section>
        <h3 className="text-lg font-medium text-zinc-200 mb-3 border-b border-zinc-700 pb-2">Requirements</h3>
        {renderArrayField('Requirements', 'requirements', 'REQ: Description')}
      </section>

      {/* Behaviors */}
      <section>
        <h3 className="text-lg font-medium text-zinc-200 mb-3 border-b border-zinc-700 pb-2">Behaviors</h3>
        <div className="space-y-4">
          {(formData.behaviors || []).map((behavior, index) => (
            <div key={index} className="p-3 bg-zinc-800/50 rounded border border-zinc-700">
              <div className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={behavior.id}
                  onChange={(e) => updateBehavior(index, { id: e.target.value })}
                  className={cn(inputClass, 'w-24')}
                  placeholder="BEH-1"
                  aria-label="Behavior ID"
                />
                <button
                  type="button"
                  onClick={() => removeBehavior(index)}
                  className="p-2 text-red-400 hover:bg-zinc-700 rounded ml-auto"
                  aria-label="Remove behavior"
                >
                  <Trash2 size={16} />
                </button>
              </div>
              <div className="space-y-2">
                <textarea
                  value={behavior.description}
                  onChange={(e) => updateBehavior(index, { description: e.target.value })}
                  rows={2}
                  className={inputClass}
                  placeholder="Behavior description..."
                  aria-label="Behavior description"
                />
                <textarea
                  value={behavior.acceptance_criteria}
                  onChange={(e) => updateBehavior(index, { acceptance_criteria: e.target.value })}
                  rows={2}
                  className={inputClass}
                  placeholder="Acceptance criteria..."
                  aria-label="Acceptance criteria"
                />
              </div>
            </div>
          ))}
          <button
            type="button"
            onClick={addBehavior}
            className="flex items-center gap-1 text-sm text-blue-400 hover:text-blue-300"
          >
            <Plus size={14} /> Add behavior
          </button>
        </div>
      </section>

      {/* Constraints */}
      <section>
        <h3 className="text-lg font-medium text-zinc-200 mb-3 border-b border-zinc-700 pb-2">Constraints</h3>
        {renderArrayField('Constraints', 'constraints', 'Constraint description')}
      </section>

      {/* Interfaces */}
      <section>
        <h3 className="text-lg font-medium text-zinc-200 mb-3 border-b border-zinc-700 pb-2">Interfaces</h3>
        {renderArrayField('Interfaces', 'interfaces', 'Interface definition')}
      </section>

      {/* Testing Requirements */}
      <section>
        <h3 className="text-lg font-medium text-zinc-200 mb-3 border-b border-zinc-700 pb-2">Testing Requirements</h3>
        {renderArrayField('Testing Requirements', 'testing_requirements', 'Test requirement')}
      </section>
    </div>
  )
}
