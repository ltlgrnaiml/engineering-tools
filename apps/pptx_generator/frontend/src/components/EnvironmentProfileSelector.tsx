import { useState } from 'react'
import type { EnvironmentProfile } from '../types'

interface EnvironmentProfileSelectorProps {
  onSelect: (profile: Partial<EnvironmentProfile>) => void
  loading: boolean
}

const PRESETS = [
  {
    id: 'local_filesystem',
    name: 'Local Filesystem',
    description: 'Use local file system for data storage',
    config: {
      name: 'Local Filesystem',
      source: 'filesystem' as const,
      roots: {
        templates_root: 'C:/Users/user/templates',
        output_root: 'C:/Users/user/output',
        dataagg_rel: '{run_key}/DataAgg/{category}',
      },
      job_context: {
        name: 'Sides',
        key: 'sides',
        values: ['Left', 'Right'],
        aliases: { l: 'Left', left: 'Left', r: 'Right', right: 'Right', L: 'Left', R: 'Right' },
      },
      encoding_policy: ['utf-8', 'utf-8-sig', 'cp1252'],
    },
  },
  {
    id: 'azure_adls',
    name: 'Azure Data Lake',
    description: 'Use Azure Data Lake Storage Gen2',
    config: {
      name: 'Azure Data Lake',
      source: 'adls' as const,
      roots: {
        templates_root: 'abfss://container/templates',
        output_root: 'abfss://container/output',
        dataagg_rel: '{run_key}/DataAgg/{category}',
      },
      job_context: {
        name: 'Wafer',
        key: 'wafer',
        values: ['W1', 'W2', 'W3'],
        aliases: { w1: 'W1', w2: 'W2', w3: 'W3', W1: 'W1', W2: 'W2', W3: 'W3' },
      },
      encoding_policy: ['utf-8', 'utf-8-sig', 'cp1252'],
    },
  },
]

export function EnvironmentProfileSelector({
  onSelect,
  loading,
}: EnvironmentProfileSelectorProps) {
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null)
  const [customMode, setCustomMode] = useState(false)

  const handlePresetSelect = (presetId: string) => {
    setSelectedPreset(presetId)
    const preset = PRESETS.find((p) => p.id === presetId)
    if (preset) {
      onSelect({ id: preset.id, ...preset.config } as Partial<EnvironmentProfile>)
    }
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Select Environment Profile
        </h2>
        <p className="text-gray-600">
          Choose where your data is stored and how it's organized
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {PRESETS.map((preset) => (
          <button
            key={preset.id}
            onClick={() => handlePresetSelect(preset.id)}
            disabled={loading}
            className={
              `p-6 border-2 rounded-lg text-left transition-all ${
                selectedPreset === preset.id
                  ? 'border-blue-600 bg-blue-50'
                  : 'border-gray-200 hover:border-blue-300'
              } ${loading ? 'opacity-50 cursor-not-allowed' : ''}`
            }
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {preset.name}
            </h3>
            <p className="text-sm text-gray-600 mb-4">{preset.description}</p>
            <div className="text-xs text-gray-500 space-y-1">
              <p>Source: {preset.config.source}</p>
              <p>Job Context: {preset.config.job_context.name}</p>
              <p>Values: {preset.config.job_context.values.join(', ')}</p>
            </div>
          </button>
        ))}
      </div>

      <div className="text-center">
        <button
          onClick={() => setCustomMode(!customMode)}
          className="text-blue-600 hover:text-blue-700 text-sm font-medium"
        >
          {customMode ? 'Hide' : 'Show'} Custom Configuration
        </button>
      </div>

      {customMode && (
        <div className="bg-gray-50 p-6 rounded-lg">
          <p className="text-sm text-gray-600">
            Custom configuration coming soon. For now, please select a preset and
            modify it after creation.
          </p>
        </div>
      )}
    </div>
  )
}
