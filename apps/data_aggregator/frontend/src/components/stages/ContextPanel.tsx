import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Settings, Loader2, Table, ChevronDown, ChevronRight, Code, FileText, Edit3 } from 'lucide-react'
import { useDebugFetch } from '../debug'
import { useProfiles, useProfileTables, useProfileContext } from '../../hooks/useProfiles'

interface ContextPanelProps {
  runId: string
}

export function ContextPanel({ runId }: ContextPanelProps) {
  const [selectedProfile, setSelectedProfile] = useState<string>('')
  const [expandedLevels, setExpandedLevels] = useState<Set<string>>(new Set(['run']))
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['regex']))
  const queryClient = useQueryClient()
  const debugFetch = useDebugFetch()

  // Fetch available profiles
  const { data: profiles, isLoading: profilesLoading } = useProfiles()
  
  // Fetch tables for selected profile (preview)
  const { data: profileTables, isLoading: tablesLoading, error: tablesError } = useProfileTables(
    selectedProfile || null
  )
  
  // Fetch context configuration for selected profile
  const { data: profileContext, isLoading: contextLoading } = useProfileContext(
    selectedProfile || null
  )
  
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
  
  const toggleLevel = (level: string) => {
    setExpandedLevels(prev => {
      const next = new Set(prev)
      if (next.has(level)) {
        next.delete(level)
      } else {
        next.add(level)
      }
      return next
    })
  }

  const lockMutation = useMutation({
    mutationFn: async () => {
      const response = await debugFetch(`/api/dat/runs/${runId}/stages/context/lock`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          profile_id: selectedProfile,
        }),
      })
      if (!response.ok) throw new Error('Failed to lock stage')
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dat-run', runId] })
    },
  })

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Context Configuration</h2>
        <p className="text-slate-600 mt-1">Select an extraction profile to define how data will be extracted.</p>
      </div>

      {/* Profile Selection */}
      <div className="bg-white rounded-lg border border-slate-200 p-4">
        <label className="block text-sm font-medium text-slate-700 mb-2">
          <Settings className="w-4 h-4 inline mr-1" />
          Extraction Profile
        </label>
        {profilesLoading ? (
          <div className="flex items-center justify-center py-4">
            <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
          </div>
        ) : (
          <div className="grid gap-3">
            {profiles?.map((profile) => (
              <label
                key={profile.id}
                className={`
                  flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors
                  ${selectedProfile === profile.id
                    ? 'border-emerald-500 bg-emerald-50'
                    : 'border-slate-200 hover:border-slate-300'
                  }
                `}
              >
                <input
                  type="radio"
                  name="profile"
                  value={profile.id}
                  checked={selectedProfile === profile.id}
                  onChange={(e) => setSelectedProfile(e.target.value)}
                  className="mt-1"
                />
                <div className="flex-1">
                  <div className="font-medium text-slate-900">{profile.name}</div>
                  <div className="text-sm text-slate-600">{profile.description}</div>
                </div>
              </label>
            ))}
          </div>
        )}
      </div>

      {/* Profile Tables Preview - shown when a profile is selected */}
      {selectedProfile && (
        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <label className="block text-sm font-medium text-slate-700 mb-3">
            <Table className="w-4 h-4 inline mr-1" />
            Tables Defined in Profile
          </label>
          {tablesLoading ? (
            <div className="flex items-center justify-center py-4">
              <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
            </div>
          ) : tablesError ? (
            <p className="text-sm text-red-500">
              Error loading tables: {tablesError instanceof Error ? tablesError.message : 'Unknown error'}
            </p>
          ) : profileTables && profileTables.levels && Object.keys(profileTables.levels).length > 0 ? (
            <div className="space-y-2">
              {Object.entries(profileTables.levels).map(([levelName, tables]) => (
                <div key={levelName} className="border border-slate-100 rounded-lg overflow-hidden">
                  <button
                    onClick={() => toggleLevel(levelName)}
                    className="w-full flex items-center justify-between p-3 bg-slate-50 hover:bg-slate-100 transition-colors"
                  >
                    <span className="font-medium text-slate-700 capitalize">
                      {levelName} Level
                      <span className="ml-2 text-sm font-normal text-slate-500">
                        ({tables.length} table{tables.length !== 1 ? 's' : ''})
                      </span>
                    </span>
                    {expandedLevels.has(levelName) ? (
                      <ChevronDown className="w-4 h-4 text-slate-400" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-slate-400" />
                    )}
                  </button>
                  {expandedLevels.has(levelName) && (
                    <div className="p-3 space-y-2">
                      {tables.map((table) => (
                        <div
                          key={table.id}
                          className="flex items-center gap-2 text-sm text-slate-600 pl-2"
                        >
                          <Table className="w-3 h-3 text-slate-400" />
                          <span className="font-medium">{table.label || table.id}</span>
                          {table.description && (
                            <span className="text-slate-400">— {table.description}</span>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              <p className="text-xs text-slate-500 mt-2">
                Total: {profileTables.total_tables} tables will be available for selection
              </p>
            </div>
          ) : (
            <p className="text-sm text-slate-500">No tables defined in this profile.</p>
          )}
        </div>
      )}

      {/* Context Configuration - Regex Patterns */}
      {selectedProfile && profileContext?.context_defaults && (
        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <button
            onClick={() => toggleSection('regex')}
            className="w-full flex items-center justify-between mb-3"
          >
            <label className="text-sm font-medium text-slate-700 flex items-center gap-2 cursor-pointer">
              <Code className="w-4 h-4" />
              Context Extraction (REGEX Patterns)
            </label>
            {expandedSections.has('regex') ? (
              <ChevronDown className="w-4 h-4 text-slate-400" />
            ) : (
              <ChevronRight className="w-4 h-4 text-slate-400" />
            )}
          </button>
          
          {contextLoading ? (
            <div className="flex items-center justify-center py-4">
              <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
            </div>
          ) : expandedSections.has('regex') && profileContext.context_defaults.regex_patterns.length > 0 ? (
            <div className="space-y-3">
              <p className="text-xs text-slate-500 mb-3">
                These patterns automatically extract context values from filenames:
              </p>
              {profileContext.context_defaults.regex_patterns.map((pattern) => (
                <div
                  key={pattern.field}
                  className="border border-slate-100 rounded-lg p-3 bg-slate-50"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-slate-800 text-sm">
                      {pattern.field}
                      {pattern.required && (
                        <span className="ml-1 text-xs text-red-500">*required</span>
                      )}
                    </span>
                    <span className="text-xs text-slate-400">{pattern.scope}</span>
                  </div>
                  <code className="block text-xs bg-slate-200 text-slate-700 px-2 py-1 rounded font-mono mb-2 overflow-x-auto">
                    {pattern.pattern}
                  </code>
                  {pattern.description && (
                    <p className="text-xs text-slate-500">{pattern.description}</p>
                  )}
                  {pattern.example && (
                    <p className="text-xs text-slate-400 mt-1">
                      Example: <span className="font-mono">{pattern.example}</span>
                    </p>
                  )}
                </div>
              ))}
            </div>
          ) : expandedSections.has('regex') ? (
            <p className="text-sm text-slate-500">No regex patterns defined.</p>
          ) : null}
        </div>
      )}

      {/* Context Defaults */}
      {selectedProfile && profileContext?.context_defaults?.defaults && 
       Object.keys(profileContext.context_defaults.defaults).length > 0 && (
        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <button
            onClick={() => toggleSection('defaults')}
            className="w-full flex items-center justify-between mb-3"
          >
            <label className="text-sm font-medium text-slate-700 flex items-center gap-2 cursor-pointer">
              <FileText className="w-4 h-4" />
              Default Values (Fallback)
            </label>
            {expandedSections.has('defaults') ? (
              <ChevronDown className="w-4 h-4 text-slate-400" />
            ) : (
              <ChevronRight className="w-4 h-4 text-slate-400" />
            )}
          </button>
          
          {expandedSections.has('defaults') && (
            <div className="space-y-2">
              <p className="text-xs text-slate-500 mb-2">
                Default values used when extraction fails:
              </p>
              {Object.entries(profileContext.context_defaults.defaults).map(([key, value]) => (
                <div
                  key={key}
                  className="flex items-center justify-between text-sm border-b border-slate-100 pb-2"
                >
                  <span className="font-medium text-slate-700">{key}</span>
                  <span className="text-slate-500 font-mono text-xs">{String(value)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Context Key Mapping */}
      {selectedProfile && profileContext?.contexts && profileContext.contexts.length > 0 && (
        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <button
            onClick={() => toggleSection('keymap')}
            className="w-full flex items-center justify-between mb-3"
          >
            <label className="text-sm font-medium text-slate-700 flex items-center gap-2 cursor-pointer">
              <Edit3 className="w-4 h-4" />
              Context Key Mapping (JSONPath)
            </label>
            {expandedSections.has('keymap') ? (
              <ChevronDown className="w-4 h-4 text-slate-400" />
            ) : (
              <ChevronRight className="w-4 h-4 text-slate-400" />
            )}
          </button>
          
          {expandedSections.has('keymap') && (
            <div className="space-y-3">
              {profileContext.contexts.map((ctx) => (
                <div key={ctx.name} className="border border-slate-100 rounded-lg p-3">
                  <div className="font-medium text-slate-700 text-sm mb-2 capitalize">
                    {ctx.name} <span className="text-slate-400 font-normal">({ctx.level} level)</span>
                  </div>
                  <div className="space-y-1">
                    {Object.entries(ctx.key_map).map(([key, path]) => (
                      <div key={key} className="flex items-center gap-2 text-xs">
                        <span className="font-medium text-slate-600 min-w-[100px]">{key}</span>
                        <span className="text-slate-400">→</span>
                        <code className="text-slate-500 font-mono bg-slate-100 px-1 rounded">
                          {path}
                        </code>
                      </div>
                    ))}
                  </div>
                  {ctx.primary_keys.length > 0 && (
                    <div className="mt-2 text-xs text-slate-400">
                      Primary keys: {ctx.primary_keys.join(', ')}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Optional Stage Notice */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm">
        <p className="text-amber-800">
          <strong>Optional Step:</strong> You can skip this configuration and use default settings, 
          or select a profile to customize the extraction.
        </p>
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-3">
        <button
          onClick={() => {
            // Skip with defaults - lock without profile selection
            lockMutation.mutate()
          }}
          disabled={lockMutation.isPending}
          className="px-6 py-2 border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg font-medium transition-colors disabled:opacity-50"
        >
          Skip with Defaults →
        </button>
        <button
          onClick={() => lockMutation.mutate()}
          disabled={!selectedProfile || lockMutation.isPending}
          className="px-6 py-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
        >
          {lockMutation.isPending ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            'Continue with Profile'
          )}
        </button>
      </div>
    </div>
  )
}
