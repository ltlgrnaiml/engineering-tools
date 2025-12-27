import { useState } from 'react'
import { ChevronDown, ChevronUp, CheckCircle, AlertCircle, Plus, Trash2, Save, Download } from 'lucide-react'
import type { DerivedRequirementsManifest, ContextMapping, MappingSuggestion } from '../types'

interface ContextMappingEditorProps {
  drm: DerivedRequirementsManifest
  dataColumns: string[]
  suggestions?: Record<string, MappingSuggestion>
  initialMappings?: ContextMapping[]
  onMappingsChange: (mappings: ContextMapping[]) => void
  onSave: () => void
  onSaveConfig?: (mappings: ContextMapping[]) => void
  saving: boolean
}

export function ContextMappingEditor({
  drm,
  dataColumns,
  suggestions = {},
  initialMappings = [],
  onMappingsChange,
  onSave,
  onSaveConfig,
  saving,
}: ContextMappingEditorProps) {
  const [mappings, setMappings] = useState<Record<string, ContextMapping>>(
    () => {
      const initial: Record<string, ContextMapping> = {}
      initialMappings.forEach((m) => {
        initial[m.context_name] = m
      })
      return initial
    }
  )
  const [expandedContext, setExpandedContext] = useState<string | null>(null)
  const [showAddForm, setShowAddForm] = useState(false)
  const [newContextName, setNewContextName] = useState('')

  const handleMappingChange = (contextName: string, mapping: ContextMapping) => {
    const updated = { ...mappings, [contextName]: mapping }
    setMappings(updated)
    onMappingsChange(Object.values(updated))
  }

  const handleRemoveMapping = (contextName: string) => {
    const updated = { ...mappings }
    delete updated[contextName]
    setMappings(updated)
    onMappingsChange(Object.values(updated))
  }

  const handleAddNewContext = () => {
    if (!newContextName.trim()) return
    const newMapping: ContextMapping = {
      context_name: newContextName.trim(),
      source_type: 'column',
      source_column: '',
    }
    const updated = { ...mappings, [newContextName.trim()]: newMapping }
    setMappings(updated)
    onMappingsChange(Object.values(updated))
    setNewContextName('')
    setShowAddForm(false)
    setExpandedContext(newContextName.trim())
  }

  const handleAcceptSuggestion = (contextName: string) => {
    const suggestion = suggestions[contextName]
    if (!suggestion) return

    const mapping: ContextMapping = {
      context_name: contextName,
      source_type: suggestion.source_type,
      source_column: suggestion.source_type === 'column' ? suggestion.suggested_source : undefined,
      regex_pattern: suggestion.source_type === 'regex' ? suggestion.suggested_source : undefined,
      default_value: suggestion.source_type === 'default' ? suggestion.suggested_source : undefined,
    }

    handleMappingChange(contextName, mapping)
  }

  const handleAcceptAllHighConfidence = () => {
    const updated = { ...mappings }
    Object.entries(suggestions).forEach(([contextName, suggestion]) => {
      if (suggestion.confidence_score >= 0.8 && !updated[contextName]) {
        updated[contextName] = {
          context_name: contextName,
          source_type: suggestion.source_type,
          source_column: suggestion.source_type === 'column' ? suggestion.suggested_source : undefined,
          regex_pattern: suggestion.source_type === 'regex' ? suggestion.suggested_source : undefined,
          default_value: suggestion.source_type === 'default' ? suggestion.suggested_source : undefined,
        }
      }
    })
    setMappings(updated)
    onMappingsChange(Object.values(updated))
  }

  const getMappingStatus = (contextName: string): 'mapped' | 'suggested' | 'unmapped' => {
    if (mappings[contextName]) return 'mapped'
    if (suggestions[contextName]?.confidence_score >= 0.5) return 'suggested'
    return 'unmapped'
  }

  const highConfidenceSuggestions = Object.values(suggestions).filter(
    (s) => s.confidence_score >= 0.8 && !mappings[s.target_name]
  ).length

  // Get all context names: from DRM required_contexts + any custom mappings
  const allContextNames = new Set([
    ...drm.required_contexts.map(c => c.name),
    ...Object.keys(mappings),
  ])

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Context Mappings</h2>
          <p className="text-gray-600 mt-1">
            Map context dimensions to your data columns. Defaults from config are pre-loaded.
          </p>
        </div>
        <div className="flex gap-2">
          {highConfidenceSuggestions > 0 && (
            <button
              onClick={handleAcceptAllHighConfidence}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Accept {highConfidenceSuggestions} Suggestions
            </button>
          )}
          <button
            onClick={() => setShowAddForm(true)}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            Add Context
          </button>
        </div>
      </div>

      <div className="bg-gray-50 p-4 rounded-lg">
        <div className="flex items-center justify-between text-sm">
          <div className="flex gap-6">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <span className="text-gray-700">
                {Object.keys(mappings).length} / {drm.required_contexts.length} Mapped
              </span>
            </div>
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-yellow-600" />
              <span className="text-gray-700">
                {Object.values(suggestions).filter(s => s.confidence_score >= 0.5).length} Suggestions
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Add New Context Form */}
      {showAddForm && (
        <div className="bg-green-50 border-2 border-green-200 rounded-lg p-4">
          <h3 className="font-semibold text-gray-900 mb-3">Add New Context</h3>
          <div className="flex gap-3">
            <input
              type="text"
              value={newContextName}
              onChange={(e) => setNewContextName(e.target.value)}
              placeholder="Enter context name (e.g., 'wafer', 'lot')..."
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
              onKeyDown={(e) => e.key === 'Enter' && handleAddNewContext()}
            />
            <button
              onClick={handleAddNewContext}
              disabled={!newContextName.trim()}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              Add
            </button>
            <button
              onClick={() => { setShowAddForm(false); setNewContextName(''); }}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="space-y-3">
        {Array.from(allContextNames).map((contextName) => {
          const drmContext = drm.required_contexts.find(c => c.name === contextName)
          const context = drmContext || { name: contextName, description: 'Custom context' }
          const isCustom = !drmContext
          return (
            <ContextMappingRow
              key={contextName}
              context={context}
              mapping={mappings[contextName]}
              suggestion={suggestions[contextName]}
              dataColumns={dataColumns}
              expanded={expandedContext === contextName}
              onToggle={() =>
                setExpandedContext(expandedContext === contextName ? null : contextName)
              }
              onChange={(mapping) => handleMappingChange(contextName, mapping)}
              onAcceptSuggestion={() => handleAcceptSuggestion(contextName)}
              onRemove={isCustom ? () => handleRemoveMapping(contextName) : undefined}
              status={getMappingStatus(contextName)}
              isCustom={isCustom}
            />
          )
        })}
      </div>

      <div className="flex justify-end gap-3 pt-4 border-t">
        {onSaveConfig && (
          <button
            onClick={() => onSaveConfig(Object.values(mappings))}
            disabled={saving || Object.keys(mappings).length === 0}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <Download className="h-4 w-4" />
            Save to Config
          </button>
        )}
        <button
          onClick={onSave}
          disabled={saving || Object.keys(mappings).length === 0}
          className={`px-6 py-2 rounded-lg font-semibold transition-colors flex items-center gap-2 ${
            Object.keys(mappings).length > 0 && !saving
              ? 'bg-green-600 text-white hover:bg-green-700'
              : 'bg-gray-300 text-gray-500 cursor-not-allowed'
          }`}
        >
          <Save className="h-4 w-4" />
          {saving ? 'Saving...' : 'Save & Continue'}
        </button>
      </div>
    </div>
  )
}

interface ContextMappingRowProps {
  context: { name: string; description?: string }
  mapping?: ContextMapping
  suggestion?: MappingSuggestion
  dataColumns: string[]
  expanded: boolean
  onToggle: () => void
  onChange: (mapping: ContextMapping) => void
  onAcceptSuggestion: () => void
  onRemove?: () => void
  status: 'mapped' | 'suggested' | 'unmapped'
  isCustom?: boolean
}

function ContextMappingRow({
  context,
  mapping,
  suggestion,
  dataColumns,
  expanded,
  onToggle,
  onChange,
  onAcceptSuggestion,
  onRemove,
  status,
  isCustom = false,
}: ContextMappingRowProps) {
  const [sourceType, setSourceType] = useState<'column' | 'regex' | 'default'>(
    mapping?.source_type || 'column'
  )
  const [sourceColumn, setSourceColumn] = useState(mapping?.source_column || '')
  const [regexPattern, setRegexPattern] = useState(mapping?.regex_pattern || '')
  const [defaultValue, setDefaultValue] = useState(mapping?.default_value || '')

  const handleApply = () => {
    const newMapping: ContextMapping = {
      context_name: context.name,
      source_type: sourceType,
      source_column: sourceType === 'column' ? sourceColumn : undefined,
      regex_pattern: sourceType === 'regex' ? regexPattern : undefined,
      default_value: sourceType === 'default' ? defaultValue : undefined,
    }
    onChange(newMapping)
  }

  const getStatusIcon = () => {
    switch (status) {
      case 'mapped':
        return <CheckCircle className="h-5 w-5 text-green-600" />
      case 'suggested':
        return <AlertCircle className="h-5 w-5 text-blue-600" />
      case 'unmapped':
        return <AlertCircle className="h-5 w-5 text-gray-400" />
    }
  }

  const getStatusBg = () => {
    switch (status) {
      case 'mapped':
        return 'bg-green-50 border-green-200'
      case 'suggested':
        return 'bg-blue-50 border-blue-200'
      case 'unmapped':
        return 'bg-white border-gray-200'
    }
  }

  return (
    <div className={`border-2 rounded-lg transition-all ${getStatusBg()}`}>
      <div
        className="p-4 flex items-center justify-between cursor-pointer"
        onClick={onToggle}
      >
        <div className="flex items-center gap-3">
          {getStatusIcon()}
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-gray-900">{context.name}</h3>
              {isCustom && (
                <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded">
                  Custom
                </span>
              )}
            </div>
            {mapping && (
              <p className="text-sm text-gray-600">
                {mapping.source_type === 'column' && `→ ${mapping.source_column}`}
                {mapping.source_type === 'regex' && `→ Regex: ${mapping.regex_pattern}`}
                {mapping.source_type === 'default' && `→ Default: ${mapping.default_value}`}
              </p>
            )}
            {!mapping && suggestion && (
              <p className="text-sm text-blue-600">
                Suggested: {suggestion.suggested_source} ({Math.round(suggestion.confidence_score * 100)}%)
              </p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {isCustom && onRemove && (
            <button
              onClick={(e) => { e.stopPropagation(); onRemove(); }}
              className="p-1 text-red-500 hover:text-red-700 hover:bg-red-50 rounded"
              title="Remove custom context"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          )}
          <button onClick={(e) => { e.stopPropagation(); onToggle(); }}>
            {expanded ? (
              <ChevronUp className="h-5 w-5 text-gray-400" />
            ) : (
              <ChevronDown className="h-5 w-5 text-gray-400" />
            )}
          </button>
        </div>
      </div>

      {expanded && (
        <div className="border-t p-4 space-y-4">
          {suggestion && !mapping && (
            <div className="bg-blue-50 p-3 rounded-lg">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-sm font-medium text-blue-900">Suggested Mapping</p>
                  <p className="text-sm text-blue-700 mt-1">{suggestion.reasoning}</p>
                  <p className="text-sm text-blue-600 mt-1">
                    Confidence: {Math.round(suggestion.confidence_score * 100)}%
                  </p>
                </div>
                <button
                  onClick={onAcceptSuggestion}
                  className="ml-3 px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                >
                  Accept
                </button>
              </div>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Source Type
            </label>
            <div className="flex gap-3">
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  value="column"
                  checked={sourceType === 'column'}
                  onChange={(e) => setSourceType(e.target.value as 'column')}
                  className="text-blue-600"
                />
                <span className="text-sm">Column</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  value="regex"
                  checked={sourceType === 'regex'}
                  onChange={(e) => setSourceType(e.target.value as 'regex')}
                  className="text-blue-600"
                />
                <span className="text-sm">Regex</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  value="default"
                  checked={sourceType === 'default'}
                  onChange={(e) => setSourceType(e.target.value as 'default')}
                  className="text-blue-600"
                />
                <span className="text-sm">Default Value</span>
              </label>
            </div>
          </div>

          {sourceType === 'column' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Data Column
              </label>
              <select
                value={sourceColumn}
                onChange={(e) => setSourceColumn(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Select a column...</option>
                {dataColumns.map((col) => (
                  <option key={col} value={col}>
                    {col}
                  </option>
                ))}
              </select>
            </div>
          )}

          {sourceType === 'regex' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Regex Pattern
              </label>
              <input
                type="text"
                value={regexPattern}
                onChange={(e) => setRegexPattern(e.target.value)}
                placeholder="e.g., DZ\d+"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                Pattern will be extracted from another column
              </p>
            </div>
          )}

          {sourceType === 'default' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Default Value
              </label>
              <input
                type="text"
                value={defaultValue}
                onChange={(e) => setDefaultValue(e.target.value)}
                placeholder="Enter default value..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          )}

          <div className="flex justify-end">
            <button
              onClick={handleApply}
              disabled={
                (sourceType === 'column' && !sourceColumn) ||
                (sourceType === 'regex' && !regexPattern) ||
                (sourceType === 'default' && !defaultValue)
              }
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                ((sourceType === 'column' && sourceColumn) ||
                  (sourceType === 'regex' && regexPattern) ||
                  (sourceType === 'default' && defaultValue))
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              Apply Mapping
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
