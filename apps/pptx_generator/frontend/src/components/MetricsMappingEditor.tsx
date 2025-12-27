import { useState } from 'react'
import { ChevronDown, ChevronUp, CheckCircle, AlertCircle, Plus, Trash2, Save, Download } from 'lucide-react'
import type { DerivedRequirementsManifest, MetricMapping, MappingSuggestion } from '../types'

interface MetricsMappingEditorProps {
  drm: DerivedRequirementsManifest
  dataColumns: string[]
  suggestions?: Record<string, MappingSuggestion>
  initialMappings?: MetricMapping[]
  onMappingsChange: (mappings: MetricMapping[]) => void
  onSave: () => void
  onSaveConfig?: (mappings: MetricMapping[]) => void
  saving: boolean
}

export function MetricsMappingEditor({
  drm,
  dataColumns,
  suggestions = {},
  initialMappings = [],
  onMappingsChange,
  onSave,
  onSaveConfig,
  saving,
}: MetricsMappingEditorProps) {
  const [mappings, setMappings] = useState<Record<string, MetricMapping>>(
    () => {
      const initial: Record<string, MetricMapping> = {}
      initialMappings.forEach((m) => {
        initial[m.metric_name] = m
      })
      return initial
    }
  )
  const [expandedMetric, setExpandedMetric] = useState<string | null>(null)
  const [showAddForm, setShowAddForm] = useState(false)
  const [newMetricName, setNewMetricName] = useState('')

  const handleMappingChange = (metricName: string, mapping: MetricMapping) => {
    const updated = { ...mappings, [metricName]: mapping }
    setMappings(updated)
    onMappingsChange(Object.values(updated))
  }

  const handleRemoveMapping = (metricName: string) => {
    const updated = { ...mappings }
    delete updated[metricName]
    setMappings(updated)
    onMappingsChange(Object.values(updated))
  }

  const handleAddNewMetric = () => {
    if (!newMetricName.trim()) return
    const newMapping: MetricMapping = {
      metric_name: newMetricName.trim(),
      source_column: '',
      aggregation_semantics: 'mean',
      data_type: 'float',
    }
    const updated = { ...mappings, [newMetricName.trim()]: newMapping }
    setMappings(updated)
    onMappingsChange(Object.values(updated))
    setNewMetricName('')
    setShowAddForm(false)
    setExpandedMetric(newMetricName.trim())
  }

  const handleAcceptSuggestion = (metricName: string) => {
    const suggestion = suggestions[metricName]
    const requiredMetric = drm.required_metrics.find(m => m.name === metricName)
    if (!suggestion || !requiredMetric) return

    const mapping: MetricMapping = {
      metric_name: metricName,
      source_column: suggestion.suggested_source,
      aggregation_semantics: requiredMetric.aggregation_type || 'mean',
      data_type: requiredMetric.data_type || 'float',
    }

    handleMappingChange(metricName, mapping)
  }

  const handleAcceptAllHighConfidence = () => {
    const updated = { ...mappings }
    Object.entries(suggestions).forEach(([metricName, suggestion]) => {
      const requiredMetric = drm.required_metrics.find(m => m.name === metricName)
      if (suggestion.confidence_score >= 0.8 && !updated[metricName] && requiredMetric) {
        updated[metricName] = {
          metric_name: metricName,
          source_column: suggestion.suggested_source,
          aggregation_semantics: requiredMetric.aggregation_type || 'mean',
          data_type: requiredMetric.data_type || 'float',
        }
      }
    })
    setMappings(updated)
    onMappingsChange(Object.values(updated))
  }

  const getMappingStatus = (metricName: string): 'mapped' | 'suggested' | 'unmapped' => {
    if (mappings[metricName]) return 'mapped'
    if (suggestions[metricName]?.confidence_score >= 0.5) return 'suggested'
    return 'unmapped'
  }

  const highConfidenceSuggestions = Object.values(suggestions).filter(
    (s) => s.confidence_score >= 0.8 && !mappings[s.target_name]
  ).length

  // Filter to only numeric columns for metrics
  const numericColumns = dataColumns.filter(col =>
    !col.toLowerCase().includes('name') &&
    !col.toLowerCase().includes('id') &&
    !col.toLowerCase().includes('file')
  )

  // Get all metric names: from DRM required_metrics + any custom mappings
  const allMetricNames = new Set([
    ...drm.required_metrics.map(m => m.name),
    ...Object.keys(mappings),
  ])

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Metrics Mappings</h2>
          <p className="text-gray-600 mt-1">
            Map metrics to your data columns. Defaults from config are pre-loaded.
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
            Add Metric
          </button>
        </div>
      </div>

      <div className="bg-gray-50 p-4 rounded-lg">
        <div className="flex items-center justify-between text-sm">
          <div className="flex gap-6">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <span className="text-gray-700">
                {Object.keys(mappings).length} / {drm.required_metrics.length} Mapped
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

      {/* Add New Metric Form */}
      {showAddForm && (
        <div className="bg-green-50 border-2 border-green-200 rounded-lg p-4">
          <h3 className="font-semibold text-gray-900 mb-3">Add New Metric</h3>
          <div className="flex gap-3">
            <input
              type="text"
              value={newMetricName}
              onChange={(e) => setNewMetricName(e.target.value)}
              placeholder="Enter metric name (e.g., 'SWR', 'LCDU')..."
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
              onKeyDown={(e) => e.key === 'Enter' && handleAddNewMetric()}
            />
            <button
              onClick={handleAddNewMetric}
              disabled={!newMetricName.trim()}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              Add
            </button>
            <button
              onClick={() => { setShowAddForm(false); setNewMetricName(''); }}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="space-y-3">
        {Array.from(allMetricNames).map((metricName) => {
          const drmMetric = drm.required_metrics.find(m => m.name === metricName)
          const metric = drmMetric || { name: metricName, description: 'Custom metric' }
          const isCustom = !drmMetric
          return (
            <MetricMappingRow
              key={metricName}
              metric={metric}
              mapping={mappings[metricName]}
              suggestion={suggestions[metricName]}
              dataColumns={numericColumns}
              expanded={expandedMetric === metricName}
              onToggle={() =>
                setExpandedMetric(expandedMetric === metricName ? null : metricName)
              }
              onChange={(mapping) => handleMappingChange(metricName, mapping)}
              onAcceptSuggestion={() => handleAcceptSuggestion(metricName)}
              onRemove={isCustom ? () => handleRemoveMapping(metricName) : undefined}
              status={getMappingStatus(metricName)}
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

interface MetricMappingRowProps {
  metric: {
    name: string
    aggregation_type?: string
    data_type?: string
    unit?: string
    description?: string
  }
  mapping?: MetricMapping
  suggestion?: MappingSuggestion
  dataColumns: string[]
  expanded: boolean
  onToggle: () => void
  onChange: (mapping: MetricMapping) => void
  onAcceptSuggestion: () => void
  onRemove?: () => void
  status: 'mapped' | 'suggested' | 'unmapped'
  isCustom?: boolean
}

function MetricMappingRow({
  metric,
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
}: MetricMappingRowProps) {
  const [sourceColumn, setSourceColumn] = useState(mapping?.source_column || '')
  const [renameTo, setRenameTo] = useState(mapping?.rename_to || '')
  const [aggregation, setAggregation] = useState<string>(
    mapping?.aggregation_semantics || metric.aggregation_type || 'mean'
  )

  const aggregationTypes = ['mean', 'median', 'std', 'min', 'max', 'sum', 'count', '3sigma']

  const handleApply = () => {
    const newMapping: MetricMapping = {
      metric_name: metric.name,
      source_column: sourceColumn,
      rename_to: renameTo || undefined,
      aggregation_semantics: aggregation as any,
      data_type: metric.data_type || 'float',
      unit: metric.unit,
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
              <h3 className="font-semibold text-gray-900">{metric.name}</h3>
              {isCustom && (
                <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded">
                  Custom
                </span>
              )}
              {metric.aggregation_type && (
                <span className="text-xs bg-gray-200 px-2 py-1 rounded">
                  {metric.aggregation_type}
                </span>
              )}
              {metric.unit && (
                <span className="text-xs text-gray-500">({metric.unit})</span>
              )}
            </div>
            {mapping && (
              <p className="text-sm text-gray-600">
                → {mapping.source_column}
                {mapping.rename_to && ` (renamed to ${mapping.rename_to})`}
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
              title="Remove custom metric"
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
              Source Column
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
            <p className="text-xs text-gray-500 mt-1">
              Select the numeric column containing this metric's data
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Aggregation Type
            </label>
            <select
              value={aggregation}
              onChange={(e) => setAggregation(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {aggregationTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                  {metric.aggregation_type === type && ' (required)'}
                </option>
              ))}
            </select>
            {aggregation !== metric.aggregation_type && metric.aggregation_type && (
              <p className="text-xs text-yellow-600 mt-1">
                ⚠️ Template requires '{metric.aggregation_type}' aggregation
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Rename To (optional)
            </label>
            <input
              type="text"
              value={renameTo}
              onChange={(e) => setRenameTo(e.target.value)}
              placeholder={`Leave empty to keep as "${metric.name}"`}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              Rename the metric in the output (e.g., "Space CD (nm)" → "SpaceCD")
            </p>
          </div>

          <div className="bg-gray-50 p-3 rounded-lg">
            <p className="text-xs font-medium text-gray-700 mb-2">Metric Details</p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-gray-500">Data Type:</span>{' '}
                <span className="text-gray-900">{metric.data_type || 'float'}</span>
              </div>
              {metric.unit && (
                <div>
                  <span className="text-gray-500">Unit:</span>{' '}
                  <span className="text-gray-900">{metric.unit}</span>
                </div>
              )}
            </div>
          </div>

          <div className="flex justify-end">
            <button
              onClick={handleApply}
              disabled={!sourceColumn}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                sourceColumn
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
