import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Settings, Loader2 } from 'lucide-react'

interface ContextPanelProps {
  runId: string
}

interface Profile {
  id: string
  name: string
  description: string
}

export function ContextPanel({ runId }: ContextPanelProps) {
  const [selectedProfile, setSelectedProfile] = useState<string>('')
  const [aggregationLevels, setAggregationLevels] = useState<string[]>([])
  const queryClient = useQueryClient()

  const { data: profiles, isLoading: profilesLoading } = useQuery({
    queryKey: ['dat-profiles'],
    queryFn: async (): Promise<Profile[]> => {
      const response = await fetch('/api/dat/profiles')
      if (!response.ok) throw new Error('Failed to fetch profiles')
      return response.json()
    },
  })

  const lockMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch(`/api/dat/runs/${runId}/stages/context/lock`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          profile_id: selectedProfile,
          aggregation_levels: aggregationLevels,
        }),
      })
      if (!response.ok) throw new Error('Failed to lock stage')
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dat-run', runId] })
    },
  })

  const aggregationOptions = ['wafer', 'lot', 'site', 'tool', 'chamber']

  const toggleAggregation = (level: string) => {
    setAggregationLevels(prev =>
      prev.includes(level)
        ? prev.filter(l => l !== level)
        : [...prev, level]
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Context Configuration</h2>
        <p className="text-slate-600 mt-1">Select profile and configure aggregation settings.</p>
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
                <div>
                  <div className="font-medium text-slate-900">{profile.name}</div>
                  <div className="text-sm text-slate-600">{profile.description}</div>
                </div>
              </label>
            ))}
          </div>
        )}
      </div>

      {/* Aggregation Levels */}
      <div className="bg-white rounded-lg border border-slate-200 p-4">
        <label className="block text-sm font-medium text-slate-700 mb-3">
          Aggregation Levels
        </label>
        <div className="flex flex-wrap gap-2">
          {aggregationOptions.map((level) => (
            <button
              key={level}
              onClick={() => toggleAggregation(level)}
              className={`
                px-4 py-2 rounded-lg text-sm font-medium transition-colors
                ${aggregationLevels.includes(level)
                  ? 'bg-emerald-500 text-white'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                }
              `}
            >
              {level}
            </button>
          ))}
        </div>
        {aggregationLevels.length > 0 && (
          <p className="mt-3 text-sm text-slate-600">
            Data will be aggregated by: {aggregationLevels.join(' → ')}
          </p>
        )}
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-3">
        <button
          onClick={() => lockMutation.mutate()}
          disabled={!selectedProfile || lockMutation.isPending}
          className="px-6 py-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
        >
          {lockMutation.isPending ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            'Continue'
          )}
        </button>
      </div>
    </div>
  )
}
