import { useState, useEffect } from 'react'
import { Settings, CheckCircle, AlertCircle, Save, RefreshCw, ChevronDown, ChevronRight, Edit2, X, Plus, Trash2 } from 'lucide-react'
import { configApi } from '../lib/api'

interface ConfigFile {
  name: string
  path: string
  size?: number
  modified?: string
}

interface ConfigValidation {
  has_job_contexts: boolean
  has_metrics: boolean
  has_defaults: boolean
  has_test_defaults: boolean
  is_valid: boolean
  errors: string[]
}

interface ConfigEditorProps {
  onConfigSelect: (config: any, filename: string) => void
  selectedConfig?: string
}

// Recursive component for editing nested objects/arrays
function ConfigValueEditor({ 
  value, 
  path, 
  onChange,
  depth = 0 
}: { 
  value: any
  path: string
  onChange: (path: string, newValue: any) => void
  depth?: number
}) {
  const [expanded, setExpanded] = useState(depth < 2)

  if (value === null || value === undefined) {
    return (
      <input
        type="text"
        value=""
        onChange={(e) => onChange(path, e.target.value || null)}
        className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
        placeholder="null"
      />
    )
  }

  if (typeof value === 'boolean') {
    return (
      <select
        value={value.toString()}
        onChange={(e) => onChange(path, e.target.value === 'true')}
        className="px-2 py-1 text-sm border border-gray-300 rounded bg-white"
      >
        <option value="true">true</option>
        <option value="false">false</option>
      </select>
    )
  }

  if (typeof value === 'number') {
    return (
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(path, parseFloat(e.target.value) || 0)}
        className="w-32 px-2 py-1 text-sm border border-gray-300 rounded"
      />
    )
  }

  if (typeof value === 'string') {
    if (value.length > 50) {
      return (
        <textarea
          value={value}
          onChange={(e) => onChange(path, e.target.value)}
          className="w-full px-2 py-1 text-sm border border-gray-300 rounded resize-y"
          rows={2}
        />
      )
    }
    return (
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(path, e.target.value)}
        className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
      />
    )
  }

  if (Array.isArray(value)) {
    return (
      <div className="border border-gray-200 rounded">
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 w-full px-2 py-1 text-sm text-left bg-gray-50 hover:bg-gray-100"
        >
          {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          <span className="text-gray-500">[{value.length} items]</span>
        </button>
        {expanded && (
          <div className="p-2 space-y-1">
            {value.map((item, idx) => (
              <div key={idx} className="flex items-start gap-2">
                <span className="text-xs text-gray-400 mt-1">{idx}:</span>
                <div className="flex-1">
                  <ConfigValueEditor
                    value={item}
                    path={`${path}[${idx}]`}
                    onChange={onChange}
                    depth={depth + 1}
                  />
                </div>
                <button
                  onClick={() => {
                    const newArr = [...value]
                    newArr.splice(idx, 1)
                    onChange(path, newArr)
                  }}
                  className="p-1 text-red-500 hover:bg-red-50 rounded"
                >
                  <Trash2 className="h-3 w-3" />
                </button>
              </div>
            ))}
            <button
              onClick={() => onChange(path, [...value, ''])}
              className="flex items-center gap-1 px-2 py-1 text-xs text-blue-600 hover:bg-blue-50 rounded"
            >
              <Plus className="h-3 w-3" /> Add item
            </button>
          </div>
        )}
      </div>
    )
  }

  if (typeof value === 'object') {
    const entries = Object.entries(value)
    return (
      <div className="border border-gray-200 rounded">
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 w-full px-2 py-1 text-sm text-left bg-gray-50 hover:bg-gray-100"
        >
          {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          <span className="text-gray-500">{`{${entries.length} fields}`}</span>
        </button>
        {expanded && (
          <div className="p-2 space-y-2">
            {entries.map(([key, val]) => (
              <div key={key} className="flex items-start gap-2">
                <span className="text-xs font-medium text-gray-600 mt-1 min-w-[80px]">{key}:</span>
                <div className="flex-1">
                  <ConfigValueEditor
                    value={val}
                    path={path ? `${path}.${key}` : key}
                    onChange={onChange}
                    depth={depth + 1}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  return <span className="text-gray-500">Unknown type</span>
}

// Section editor for top-level config sections
function ConfigSection({
  title,
  data,
  expanded,
  onToggle,
  onChange,
}: {
  title: string
  data: any
  expanded: boolean
  onToggle: () => void
  onChange: (key: string, value: any) => void
}) {
  if (data === undefined || data === null) return null

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        onClick={onToggle}
        className="flex items-center justify-between w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 text-left"
      >
        <span className="font-medium text-gray-900">{title}</span>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">
            {typeof data === 'object' ? Object.keys(data).length + ' fields' : typeof data}
          </span>
          {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        </div>
      </button>
      {expanded && (
        <div className="p-4 bg-white max-h-96 overflow-y-auto">
          {typeof data === 'object' && !Array.isArray(data) ? (
            <div className="space-y-3">
              {Object.entries(data).map(([key, value]) => (
                <div key={key} className="flex items-start gap-3">
                  <label className="text-sm font-medium text-gray-700 min-w-[140px] mt-1">
                    {key}
                  </label>
                  <div className="flex-1">
                    <ConfigValueEditor
                      value={value}
                      path={key}
                      onChange={(path, newVal) => {
                        if (path === key) {
                          onChange(key, newVal)
                        } else {
                          // Handle nested path updates
                          const newData = JSON.parse(JSON.stringify(data))
                          setNestedValue(newData, path, newVal)
                          onChange(key, newData[key])
                        }
                      }}
                      depth={1}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <ConfigValueEditor
              value={data}
              path=""
              onChange={(_, newVal) => onChange(title.toLowerCase().replace(/ /g, '_'), newVal)}
              depth={0}
            />
          )}
        </div>
      )}
    </div>
  )
}

// Helper to set nested value by path
function setNestedValue(obj: any, path: string, value: any) {
  const parts = path.replace(/\[(\d+)\]/g, '.$1').split('.')
  let current = obj
  for (let i = 0; i < parts.length - 1; i++) {
    const key = parts[i]
    if (!(key in current)) {
      current[key] = {}
    }
    current = current[key]
  }
  current[parts[parts.length - 1]] = value
}

export function ConfigEditor({ onConfigSelect, selectedConfig }: ConfigEditorProps) {
  const [configFiles, setConfigFiles] = useState<ConfigFile[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedFile, setSelectedFile] = useState<string>(selectedConfig || '')
  const [loadedConfig, setLoadedConfig] = useState<any>(null)
  const [editedConfig, setEditedConfig] = useState<any>(null)
  const [validation, setValidation] = useState<ConfigValidation | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [showEditor, setShowEditor] = useState(false)
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['job_contexts', 'metrics', 'defaults']))
  const [showSaveDialog, setShowSaveDialog] = useState(false)
  const [saveFilename, setSaveFilename] = useState('')
  const [overwrite, setOverwrite] = useState(false)
  const [saving, setSaving] = useState(false)
  const [hasChanges, setHasChanges] = useState(false)

  useEffect(() => {
    loadConfigList()
  }, [])

  const loadConfigList = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await configApi.listConfigFiles()
      setConfigFiles(result.files)
    } catch (err) {
      setError('Failed to load config files')
      console.error('Failed to load config files:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSelectConfig = async (filename: string) => {
    if (!filename) return

    setLoading(true)
    setError(null)
    try {
      const result = await configApi.loadConfigFile(filename)
      setSelectedFile(filename)
      setLoadedConfig(result.config)
      setEditedConfig(JSON.parse(JSON.stringify(result.config))) // Deep copy for editing
      setValidation(result.validation)
      setHasChanges(false)
      onConfigSelect(result.config, filename)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load config file')
      console.error('Failed to load config:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSectionChange = (sectionKey: string, fieldKey: string, value: any) => {
    setEditedConfig((prev: any) => {
      const updated = { ...prev }
      if (!updated[sectionKey]) {
        updated[sectionKey] = {}
      }
      updated[sectionKey] = { ...updated[sectionKey], [fieldKey]: value }
      return updated
    })
    setHasChanges(true)
  }

  const toggleSection = (section: string) => {
    setExpandedSections(prev => {
      const next = new Set(prev)
      if (next.has(section)) {
        next.delete(section)
      } else {
        next.add(section)
      }
      return next
    })
  }

  const handleSave = async () => {
    if (!saveFilename.trim() || !editedConfig) return

    setSaving(true)
    setError(null)
    try {
      let filename = saveFilename
      if (!filename.endsWith('.yaml')) {
        filename = `${filename}.yaml`
      }

      await configApi.saveFullConfig({
        filename,
        config: editedConfig,
        overwrite,
      })

      setShowSaveDialog(false)
      setSaveFilename('')
      setOverwrite(false)
      setHasChanges(false)
      setLoadedConfig(JSON.parse(JSON.stringify(editedConfig)))

      // Reload config list
      await loadConfigList()

      // If saved to same file, update selected
      if (filename === selectedFile) {
        setLoadedConfig(editedConfig)
      } else {
        setSelectedFile(filename)
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to save config file')
    } finally {
      setSaving(false)
    }
  }

  const openSaveDialog = () => {
    setSaveFilename(selectedFile || 'new_config.yaml')
    setOverwrite(!!selectedFile)
    setShowSaveDialog(true)
  }

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return ''
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  // Get top-level sections for the editor
  const configSections = editedConfig ? Object.keys(editedConfig) : []

  return (
    <div className="bg-white rounded-lg border border-gray-200">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <Settings className="h-5 w-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">Configuration</h3>
        </div>
        <div className="flex items-center gap-2">
          {hasChanges && (
            <span className="text-xs text-orange-600 bg-orange-50 px-2 py-1 rounded">
              Unsaved changes
            </span>
          )}
          <button
            onClick={loadConfigList}
            disabled={loading}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
            title="Refresh config list"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Config file selector */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex gap-3">
          <select
            value={selectedFile}
            onChange={(e) => handleSelectConfig(e.target.value)}
            disabled={loading}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">-- Select a config file --</option>
            {configFiles.map((file) => (
              <option key={file.name} value={file.name}>
                {file.name} {file.size ? `(${formatFileSize(file.size)})` : ''}
              </option>
            ))}
          </select>
          {loadedConfig && (
            <button
              onClick={() => setShowEditor(!showEditor)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                showEditor 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <Edit2 className="h-4 w-4" />
              {showEditor ? 'Close Editor' : 'Edit Config'}
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border-b border-red-200 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Validation status */}
      {validation && (
        <div className="p-4 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center gap-2 mb-2">
            {validation.is_valid ? (
              <CheckCircle className="h-5 w-5 text-green-500" />
            ) : (
              <AlertCircle className="h-5 w-5 text-yellow-500" />
            )}
            <span className={`font-medium ${validation.is_valid ? 'text-green-700' : 'text-yellow-700'}`}>
              {validation.is_valid ? 'Configuration Valid' : 'Configuration Has Issues'}
            </span>
          </div>

          <div className="grid grid-cols-4 gap-2 text-sm">
            <div className="flex items-center gap-1">
              {validation.has_job_contexts ? (
                <CheckCircle className="h-4 w-4 text-green-500" />
              ) : (
                <AlertCircle className="h-4 w-4 text-red-500" />
              )}
              <span>Job Contexts</span>
            </div>
            <div className="flex items-center gap-1">
              {validation.has_metrics ? (
                <CheckCircle className="h-4 w-4 text-green-500" />
              ) : (
                <AlertCircle className="h-4 w-4 text-gray-400" />
              )}
              <span>Metrics</span>
            </div>
            <div className="flex items-center gap-1">
              {validation.has_defaults ? (
                <CheckCircle className="h-4 w-4 text-green-500" />
              ) : (
                <AlertCircle className="h-4 w-4 text-gray-400" />
              )}
              <span>Defaults</span>
            </div>
            <div className="flex items-center gap-1">
              {validation.has_test_defaults ? (
                <CheckCircle className="h-4 w-4 text-green-500" />
              ) : (
                <AlertCircle className="h-4 w-4 text-gray-400" />
              )}
              <span>Test Defaults</span>
            </div>
          </div>

          {validation.errors.length > 0 && (
            <div className="mt-2 text-sm text-red-600">
              {validation.errors.map((err, idx) => (
                <div key={idx}>• {err}</div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Config Editor Panel */}
      {showEditor && editedConfig && (
        <div className="p-4 border-b border-gray-200 bg-white">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-medium text-gray-900">Edit Configuration</h4>
            <div className="flex items-center gap-2">
              <button
                onClick={() => {
                  setEditedConfig(JSON.parse(JSON.stringify(loadedConfig)))
                  setHasChanges(false)
                }}
                disabled={!hasChanges}
                className="px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-lg disabled:opacity-50"
              >
                Reset
              </button>
              <button
                onClick={openSaveDialog}
                disabled={!hasChanges}
                className="flex items-center gap-1 px-3 py-1.5 text-sm bg-blue-600 text-white hover:bg-blue-700 rounded-lg disabled:bg-gray-300"
              >
                <Save className="h-4 w-4" />
                Save
              </button>
            </div>
          </div>

          <div className="space-y-3 max-h-[500px] overflow-y-auto">
            {configSections.map((section) => (
              <ConfigSection
                key={section}
                title={section}
                data={editedConfig[section]}
                expanded={expandedSections.has(section)}
                onToggle={() => toggleSection(section)}
                onChange={(key, value) => handleSectionChange(section, key, value)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Save dialog */}
      {showSaveDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-w-full mx-4 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-lg font-semibold">Save Configuration</h4>
              <button
                onClick={() => setShowSaveDialog(false)}
                className="p-1 hover:bg-gray-100 rounded"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Filename
              </label>
              <input
                type="text"
                value={saveFilename}
                onChange={(e) => setSaveFilename(e.target.value)}
                placeholder="my_config.yaml"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="mb-4">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={overwrite}
                  onChange={(e) => setOverwrite(e.target.checked)}
                  className="rounded border-gray-300"
                />
                <span className="text-sm text-gray-700">Overwrite if exists</span>
              </label>
            </div>

            {error && (
              <div className="mb-4 p-2 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
                {error}
              </div>
            )}

            <div className="flex justify-end gap-2">
              <button
                onClick={() => {
                  setShowSaveDialog(false)
                  setError(null)
                }}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving || !saveFilename.trim()}
                className="px-4 py-2 bg-blue-600 text-white hover:bg-blue-700 rounded-lg disabled:bg-gray-300"
              >
                {saving ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
