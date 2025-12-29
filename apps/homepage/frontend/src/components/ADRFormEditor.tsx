import { useState, useEffect } from 'react'
import { AlertCircle, CheckCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ADRFormData {
  [key: string]: string | string[] | Record<string, unknown> | unknown
}

interface ADRFormEditorProps {
  adr: ADRFormData | null
  isNewAdr?: boolean
  onSave: (data: ADRFormData) => Promise<void>
  onValidate?: () => Promise<void>
}

interface FieldError {
  [key: string]: string | null
}

const API_BASE = 'http://localhost:8000/api/devtools'

export function ADRFormEditor({ adr, isNewAdr = false, onSave }: ADRFormEditorProps) {
  const [formData, setFormData] = useState<ADRFormData>({})
  const [fieldErrors, setFieldErrors] = useState<FieldError>({})
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    if (adr) {
      setFormData(adr)
    } else if (isNewAdr) {
      // Initialize with defaults for new ADR
      setFormData({
        schema_type: 'adr',
        id: '',
        title: '',
        status: 'proposed',
        date: new Date().toISOString().split('T')[0],
        review_date: '',
        deciders: 'CDU-DAT Core Engineering Team',
        scope: 'core',
        context: '',
        decision_primary: '',
        decision_details: {
          approach: '',
          constraints: [],
          implementation_specs: [],
        },
        consequences: [],
        alternatives_considered: [],
        tradeoffs: '',
        guardrails: [],
        cross_cutting_guardrails: [],
        references: [],
        tags: [],
        affected_components: [],
        provenance: [],
      })
    }
  }, [adr, isNewAdr])

  const validateField = async (fieldName: string, value: unknown) => {
    try {
      const response = await fetch(`${API_BASE}/adrs/validate-field`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          field_name: fieldName,
          field_value: value,
          context: formData,
        }),
      })
      if (response.ok) {
        const result = await response.json()
        setFieldErrors((prev) => ({ ...prev, [fieldName]: result.error }))
      }
    } catch (error) {
      console.error('Field validation failed:', error)
    }
  }

  const handleFieldChange = (fieldName: string, value: unknown) => {
    setFormData((prev) => ({ ...prev, [fieldName]: value }))
    // Debounce validation
    setTimeout(() => validateField(fieldName, value), 500)
  }

  const handleNestedFieldChange = (parent: string, child: string, value: unknown) => {
    setFormData((prev) => ({
      ...prev,
      [parent]: {
        ...(prev[parent] || {}),
        [child]: value,
      },
    }))
  }

  const handleArrayFieldChange = (fieldName: string, index: number, value: string) => {
    setFormData((prev) => {
      const arr = [...((prev[fieldName] as string[]) || [])]
      arr[index] = value
      return { ...prev, [fieldName]: arr }
    })
  }

  const addArrayItem = (fieldName: string) => {
    setFormData((prev) => ({
      ...prev,
      [fieldName]: [...((prev[fieldName] as string[]) || []), ''],
    }))
  }

  const removeArrayItem = (fieldName: string, index: number) => {
    setFormData((prev) => ({
      ...prev,
      [fieldName]: ((prev[fieldName] as string[]) || []).filter((_: string, i: number) => i !== index),
    }))
  }

  const handleSubmit = async () => {
    setIsSaving(true)
    try {
      await onSave(formData)
    } finally {
      setIsSaving(false)
    }
  }

  const renderField = (
    label: string,
    fieldName: string,
    type: 'text' | 'textarea' | 'select' | 'date' = 'text',
    options?: string[],
    required = false
  ) => {
    const value = (formData[fieldName] as string) || ''
    const error = fieldErrors[fieldName]

    return (
      <div className="space-y-1">
        <label className="block text-sm font-medium text-slate-700">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
        {type === 'textarea' ? (
          <textarea
            value={value as string}
            onChange={(e) => handleFieldChange(fieldName, e.target.value)}
            className={cn(
              'w-full px-3 py-2 border rounded-md text-sm resize-y min-h-[80px]',
              error ? 'border-red-300 focus:ring-red-500' : 'border-slate-300 focus:ring-primary-500'
            )}
            placeholder={`Enter ${label.toLowerCase()}...`}
          />
        ) : type === 'select' ? (
          <select
            value={value as string}
            onChange={(e) => handleFieldChange(fieldName, e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:ring-primary-500"
            aria-label={label}
          >
            {options?.map((opt) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </select>
        ) : (
          <input
            type={type}
            value={value as string}
            onChange={(e) => handleFieldChange(fieldName, e.target.value)}
            className={cn(
              'w-full px-3 py-2 border rounded-md text-sm',
              error ? 'border-red-300 focus:ring-red-500' : 'border-slate-300 focus:ring-primary-500'
            )}
            placeholder={`Enter ${label.toLowerCase()}...`}
          />
        )}
        {error && (
          <div className="flex items-center gap-1 text-xs text-red-600">
            <AlertCircle className="w-3 h-3" />
            {error}
          </div>
        )}
        {!error && value && (
          <div className="flex items-center gap-1 text-xs text-green-600">
            <CheckCircle className="w-3 h-3" />
            Valid
          </div>
        )}
      </div>
    )
  }

  const renderArrayField = (label: string, fieldName: string) => {
    const items = (formData[fieldName] || []) as string[]

    return (
      <div className="space-y-2">
        <label className="block text-sm font-medium text-slate-700">{label}</label>
        {items.map((item, index) => (
          <div key={index} className="flex gap-2">
            <input
              type="text"
              value={item}
              onChange={(e) => handleArrayFieldChange(fieldName, index, e.target.value)}
              className="flex-1 px-3 py-2 border border-slate-300 rounded-md text-sm focus:ring-primary-500"
              placeholder={`${label} item ${index + 1}...`}
            />
            <button
              onClick={() => removeArrayItem(fieldName, index)}
              className="px-3 py-2 bg-red-50 text-red-600 rounded-md text-sm hover:bg-red-100"
            >
              Remove
            </button>
          </div>
        ))}
        <button
          onClick={() => addArrayItem(fieldName)}
          className="px-3 py-2 bg-slate-100 text-slate-700 rounded-md text-sm hover:bg-slate-200"
        >
          + Add {label}
        </button>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between p-3 border-b border-slate-200 bg-slate-50">
        <h3 className="font-semibold text-slate-900">{isNewAdr ? 'Create New ADR' : 'Edit ADR'}</h3>
        <button
          onClick={handleSubmit}
          disabled={isSaving}
          className="px-4 py-2 bg-primary-600 text-white rounded-md text-sm font-medium hover:bg-primary-700 disabled:opacity-50"
        >
          {isSaving ? 'Saving...' : 'Save ADR'}
        </button>
      </div>

      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-3xl mx-auto space-y-6">
          {/* Core Information */}
          <section className="space-y-4">
            <h4 className="text-lg font-semibold text-slate-900 border-b pb-2">Core Information</h4>
            {renderField('ADR ID', 'id', 'text', undefined, true)}
            {renderField('Title', 'title', 'text', undefined, true)}
            {renderField('Status', 'status', 'select', ['proposed', 'accepted', 'deprecated', 'superseded'], true)}
            {renderField('Date', 'date', 'date', undefined, true)}
            {renderField('Review Date', 'review_date', 'date')}
            {renderField('Deciders', 'deciders', 'text', undefined, true)}
            {renderField(
              'Scope',
              'scope',
              'select',
              ['core', 'subsystem:DAT', 'subsystem:PPTX', 'subsystem:SOV', 'subsystem:DevTools'],
              true
            )}
          </section>

          {/* Decision Content */}
          <section className="space-y-4">
            <h4 className="text-lg font-semibold text-slate-900 border-b pb-2">Decision Content</h4>
            {renderField('Context', 'context', 'textarea', undefined, true)}
            {renderField('Decision (Primary)', 'decision_primary', 'textarea', undefined, true)}
            <div className="space-y-3">
              <label className="block text-sm font-medium text-slate-700">Decision Details</label>
              <input
                type="text"
                value={((formData.decision_details as Record<string, unknown>)?.approach as string) || ''}
                onChange={(e) => handleNestedFieldChange('decision_details', 'approach', e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm"
                placeholder="Approach..."
              />
            </div>
            {renderField('Tradeoffs', 'tradeoffs', 'textarea')}
          </section>

          {/* Lists */}
          <section className="space-y-4">
            <h4 className="text-lg font-semibold text-slate-900 border-b pb-2">Consequences & Alternatives</h4>
            {renderArrayField('Consequences', 'consequences')}
            {renderArrayField('Cross-Cutting Guardrails', 'cross_cutting_guardrails')}
          </section>

          {/* References */}
          <section className="space-y-4">
            <h4 className="text-lg font-semibold text-slate-900 border-b pb-2">References & Metadata</h4>
            {renderArrayField('References', 'references')}
            {renderArrayField('Tags', 'tags')}
            {renderArrayField('Affected Components', 'affected_components')}
          </section>
        </div>
      </div>
    </div>
  )
}
