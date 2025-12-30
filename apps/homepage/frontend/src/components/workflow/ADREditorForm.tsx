import { useState, useEffect, useCallback } from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ADRFormData {
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
  alternatives_considered?: string[]
  tradeoffs?: string
  guardrails?: string[]
  cross_cutting_guardrails?: string[]
  references?: string[]
  tags?: string[]
  affected_components?: string[]
  [key: string]: unknown
}

interface ADREditorFormProps {
  content: string
  onChange: (content: string) => void
  className?: string
}

const STATUS_OPTIONS = ['draft', 'proposed', 'active', 'deprecated', 'superseded']
const SCOPE_OPTIONS = ['core', 'dat', 'pptx', 'sov', 'devtools', 'shared']

export function ADREditorForm({ content, onChange, className }: ADREditorFormProps) {
  const [formData, setFormData] = useState<ADRFormData>({})

  useEffect(() => {
    try {
      setFormData(JSON.parse(content))
    } catch {
      setFormData({})
    }
  }, [content])

  const updateForm = useCallback((updates: Partial<ADRFormData>) => {
    const updated = { ...formData, ...updates }
    setFormData(updated)
    onChange(JSON.stringify(updated, null, 2))
  }, [formData, onChange])

  const handleFieldChange = (field: string, value: unknown) => {
    updateForm({ [field]: value })
  }

  const handleNestedChange = (parent: string, child: string, value: unknown) => {
    const parentObj = (formData[parent] as Record<string, unknown>) || {}
    updateForm({ [parent]: { ...parentObj, [child]: value } })
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

  const inputClass = 'w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded focus:outline-none focus:border-blue-500 text-sm'
  const labelClass = 'block text-sm text-zinc-400 mb-1'

  const renderTextField = (label: string, field: string, required = false) => (
    <div>
      <label htmlFor={`adr-${field}`} className={labelClass}>
        {label}{required && <span className="text-red-400 ml-1">*</span>}
      </label>
      <input
        id={`adr-${field}`}
        type="text"
        value={String(formData[field] || '')}
        onChange={(e) => handleFieldChange(field, e.target.value)}
        className={inputClass}
        aria-label={label}
      />
    </div>
  )

  const renderTextArea = (label: string, field: string, rows = 4) => (
    <div>
      <label htmlFor={`adr-${field}`} className={labelClass}>{label}</label>
      <textarea
        id={`adr-${field}`}
        value={String(formData[field] || '')}
        onChange={(e) => handleFieldChange(field, e.target.value)}
        rows={rows}
        className={inputClass}
        aria-label={label}
      />
    </div>
  )

  const renderSelect = (label: string, field: string, options: string[]) => (
    <div>
      <label htmlFor={`adr-${field}`} className={labelClass}>{label}</label>
      <select
        id={`adr-${field}`}
        value={String(formData[field] || options[0])}
        onChange={(e) => handleFieldChange(field, e.target.value)}
        className={inputClass}
        aria-label={label}
      >
        {options.map(opt => <option key={opt} value={opt}>{opt}</option>)}
      </select>
    </div>
  )

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

  const renderNestedArrayField = (label: string, parent: string, child: string, placeholder = 'Add item...') => {
    const parentObj = (formData[parent] as Record<string, unknown>) || {}
    const items = (parentObj[child] as string[]) || []
    
    const handleChange = (index: number, value: string) => {
      const arr = [...items]
      arr[index] = value
      handleNestedChange(parent, child, arr)
    }
    
    const handleAdd = () => {
      handleNestedChange(parent, child, [...items, ''])
    }
    
    const handleRemove = (index: number) => {
      handleNestedChange(parent, child, items.filter((_, i) => i !== index))
    }
    
    return (
      <div>
        <label className={labelClass}>{label}</label>
        <div className="space-y-2">
          {items.map((item, i) => (
            <div key={i} className="flex gap-2">
              <input
                type="text"
                value={item}
                onChange={(e) => handleChange(i, e.target.value)}
                placeholder={placeholder}
                className={cn(inputClass, 'flex-1')}
                aria-label={`${label} item ${i + 1}`}
              />
              <button
                type="button"
                onClick={() => handleRemove(i)}
                className="p-2 text-red-400 hover:bg-zinc-800 rounded"
                aria-label={`Remove ${label} item`}
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))}
          <button
            type="button"
            onClick={handleAdd}
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
          {renderTextField('ID', 'id', true)}
          {renderTextField('Title', 'title', true)}
        </div>
        <div className="grid grid-cols-3 gap-4 mt-4">
          {renderSelect('Status', 'status', STATUS_OPTIONS)}
          {renderSelect('Scope', 'scope', SCOPE_OPTIONS)}
          <div>
            <label htmlFor="adr-date" className={labelClass}>Date</label>
            <input
              id="adr-date"
              type="date"
              value={String(formData.date || '')}
              onChange={(e) => handleFieldChange('date', e.target.value)}
              className={inputClass}
              aria-label="Date"
            />
          </div>
        </div>
        <div className="mt-4">
          {renderTextField('Deciders', 'deciders')}
        </div>
      </section>

      {/* Context & Decision Section */}
      <section>
        <h3 className="text-lg font-medium text-zinc-200 mb-3 border-b border-zinc-700 pb-2">Context & Decision</h3>
        {renderTextArea('Context', 'context', 5)}
        <div className="mt-4">
          {renderTextArea('Primary Decision', 'decision_primary', 4)}
        </div>
        <div className="mt-4">
          <label className={labelClass}>Decision Details - Approach</label>
          <textarea
            value={String(formData.decision_details?.approach || '')}
            onChange={(e) => handleNestedChange('decision_details', 'approach', e.target.value)}
            rows={3}
            className={inputClass}
            aria-label="Decision approach"
          />
        </div>
      </section>

      {/* Constraints & Implementation */}
      <section>
        <h3 className="text-lg font-medium text-zinc-200 mb-3 border-b border-zinc-700 pb-2">Constraints & Implementation</h3>
        {renderNestedArrayField('Constraints', 'decision_details', 'constraints', 'Add constraint...')}
        <div className="mt-4">
          {renderNestedArrayField('Implementation Specs', 'decision_details', 'implementation_specs', 'Add spec...')}
        </div>
      </section>

      {/* Consequences & Alternatives */}
      <section>
        <h3 className="text-lg font-medium text-zinc-200 mb-3 border-b border-zinc-700 pb-2">Consequences & Alternatives</h3>
        {renderArrayField('Consequences', 'consequences', 'Add consequence...')}
        <div className="mt-4">
          {renderArrayField('Alternatives Considered', 'alternatives_considered', 'Add alternative...')}
        </div>
        <div className="mt-4">
          {renderTextArea('Tradeoffs', 'tradeoffs', 3)}
        </div>
      </section>

      {/* Guardrails */}
      <section>
        <h3 className="text-lg font-medium text-zinc-200 mb-3 border-b border-zinc-700 pb-2">Guardrails</h3>
        {renderArrayField('Guardrails', 'guardrails', 'Add guardrail...')}
        <div className="mt-4">
          {renderArrayField('Cross-Cutting Guardrails', 'cross_cutting_guardrails', 'Add cross-cutting guardrail...')}
        </div>
      </section>

      {/* Metadata */}
      <section>
        <h3 className="text-lg font-medium text-zinc-200 mb-3 border-b border-zinc-700 pb-2">Metadata</h3>
        {renderArrayField('Tags', 'tags', 'Add tag...')}
        <div className="mt-4">
          {renderArrayField('Affected Components', 'affected_components', 'Add component...')}
        </div>
        <div className="mt-4">
          {renderArrayField('References', 'references', 'Add reference...')}
        </div>
      </section>
    </div>
  )
}
