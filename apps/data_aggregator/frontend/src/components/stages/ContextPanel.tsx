import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Settings, Loader2, Table, ChevronDown, ChevronRight } from 'lucide-react'
import { useDebugFetch } from '../debug'
import { useProfiles, useProfileTables } from '../../hooks/useProfiles'

interface ContextPanelProps {
  runId: string
}

export function ContextPanel({ runId }: ContextPanelProps) {
  const [selectedProfile, setSelectedProfile] = useState<string>('')
  const [expandedLevels, setExpandedLevels] = useState<Set<string>>(new Set(['run']))
  const queryClient = useQueryClient()
  const debugFetch = useDebugFetch()

  // Fetch available profiles
  const { data: profiles, isLoading: profilesLoading } = useProfiles()
  
  // Fetch tables for selected profile (preview)
  const { data: profileTables, isLoading: tablesLoading, error: tablesError } = useProfileTables(
    selectedProfile || null
  )
  
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
