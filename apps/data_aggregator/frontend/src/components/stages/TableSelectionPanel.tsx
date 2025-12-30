import { useState, useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Table, Check, Loader2, ChevronDown, ChevronRight, Settings2 } from 'lucide-react'
import { useDebugFetch } from '../debug'
import { useProfileTables } from '../../hooks/useProfiles'
import type { ContextOptions } from '../../types/profile'

interface TableSelectionPanelProps {
  runId: string
}

interface TableInfo {
  name: string
  file: string
  row_count: number
  column_count: number
}

export function TableSelectionPanel({ runId }: TableSelectionPanelProps) {
  const [selectedTables, setSelectedTables] = useState<Set<string>>(new Set())
  const [expandedLevels, setExpandedLevels] = useState<Set<string>>(new Set(['run', 'image']))
  const [contextOptions, setContextOptions] = useState<ContextOptions>({
    includeRunContext: true,
    includeImageContext: false,
  })
  const queryClient = useQueryClient()
  const debugFetch = useDebugFetch()

  // Get profile_id from run state (includes context stage artifact)
  const { data: runState } = useQuery({
    queryKey: ['dat-run', runId],
    queryFn: async () => {
      const response = await debugFetch(`/api/dat/runs/${runId}`)
      if (!response.ok) throw new Error('Failed to fetch run')
      return response.json()
    },
  })

  // Profile ID can come from run state OR context stage artifact
  const profileId = runState?.profile_id || runState?.stages?.context?.artifact?.profile_id

  // Fetch profile-defined tables if profile is set
  const { data: profileTables, isLoading: profileTablesLoading } = useProfileTables(profileId)

  // Fallback: fetch file-based tables if no profile
  const { data: fileTables, isLoading: fileTablesLoading } = useQuery({
    queryKey: ['dat-available-tables', runId],
    queryFn: async (): Promise<TableInfo[]> => {
      const response = await debugFetch(`/api/dat/runs/${runId}/stages/table_selection/tables`)
      if (!response.ok) throw new Error('Failed to fetch tables')
      return response.json()
    },
    enabled: !profileId,
  })

  const isLoading = profileId ? profileTablesLoading : fileTablesLoading

  // Auto-select default tables from profile UI config
  useEffect(() => {
    if (profileTables?.ui?.table_selection?.default_selected) {
      setSelectedTables(new Set(profileTables.ui.table_selection.default_selected))
    }
  }, [profileTables])

  // Set default context options from profile UI config
  useEffect(() => {
    if (profileTables?.ui?.context_options) {
      setContextOptions({
        includeRunContext: profileTables.ui.context_options.default_include_run_context ?? true,
        includeImageContext: profileTables.ui.context_options.default_include_image_context ?? false,
      })
    }
  }, [profileTables])

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
      // For profile-based extraction, send table IDs
      // For file-based extraction, group by file
      const payload = profileId
        ? {
            selected_tables: { profile: Array.from(selectedTables) },
            context_options: {
              include_run_context: contextOptions.includeRunContext,
              include_image_context: contextOptions.includeImageContext,
            },
          }
        : {
            selected_tables: groupTablesByFile(Array.from(selectedTables), fileTables || []),
            context_options: {
              include_run_context: contextOptions.includeRunContext,
              include_image_context: contextOptions.includeImageContext,
            },
          }

      const response = await debugFetch(`/api/dat/runs/${runId}/stages/table_selection/lock`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!response.ok) throw new Error('Failed to lock stage')
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dat-run', runId] })
    },
  })

  const toggleTable = (tableId: string) => {
    setSelectedTables(prev => {
      const newSet = new Set(prev)
      if (newSet.has(tableId)) {
        newSet.delete(tableId)
      } else {
        newSet.add(tableId)
      }
      return newSet
    })
  }

  const selectAllInLevel = (levelTables: { id: string }[]) => {
    setSelectedTables(prev => {
      const newSet = new Set(prev)
      levelTables.forEach(t => newSet.add(t.id))
      return newSet
    })
  }

  const selectNoneInLevel = (levelTables: { id: string }[]) => {
    setSelectedTables(prev => {
      const newSet = new Set(prev)
      levelTables.forEach(t => newSet.delete(t.id))
      return newSet
    })
  }

  const selectAll = () => {
    if (profileTables) {
      const allIds = Object.values(profileTables.levels).flat().map(t => t.id)
      setSelectedTables(new Set(allIds))
    } else if (fileTables) {
      setSelectedTables(new Set(fileTables.map(t => t.name)))
    }
  }

  const selectNone = () => {
    setSelectedTables(new Set())
  }

  // Helper to group tables by file for legacy file-based extraction
  const groupTablesByFile = (tableNames: string[], tables: TableInfo[]): Record<string, string[]> => {
    const grouped: Record<string, string[]> = {}
    tableNames.forEach(name => {
      const table = tables.find(t => t.name === name)
      if (table) {
        if (!grouped[table.file]) grouped[table.file] = []
        grouped[table.file].push(name)
      }
    })
    return grouped
  }

  const totalTables = profileTables
    ? profileTables.total_tables
    : (fileTables?.length || 0)

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Table Selection</h2>
        <p className="text-slate-600 mt-1">
          {profileId
            ? 'Choose which profile-defined tables to extract.'
            : 'Choose which tables to include in the aggregation.'}
        </p>
      </div>

      {/* Selection Controls */}
      <div className="flex items-center justify-between">
        <span className="text-sm text-slate-600">
          {selectedTables.size} of {totalTables} tables selected
        </span>
        <div className="flex gap-2">
          <button
            onClick={selectAll}
            className="text-sm text-emerald-600 hover:text-emerald-700 font-medium"
          >
            Select All
          </button>
          <span className="text-slate-300">|</span>
          <button
            onClick={selectNone}
            className="text-sm text-slate-600 hover:text-slate-700 font-medium"
          >
            Clear
          </button>
        </div>
      </div>

      {/* Profile-based Table Selection (grouped by level) */}
      {profileId && profileTables && !isLoading && (
        <div className="space-y-3">
          {Object.entries(profileTables.levels).map(([levelName, tables]) => (
            <div key={levelName} className="bg-white rounded-lg border border-slate-200 overflow-hidden">
              {/* Level Header */}
              <button
                onClick={() => toggleLevel(levelName)}
                className="w-full flex items-center justify-between p-4 bg-slate-50 hover:bg-slate-100 transition-colors"
              >
                <div className="flex items-center gap-3">
                  {expandedLevels.has(levelName) ? (
                    <ChevronDown className="w-4 h-4 text-slate-400" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-slate-400" />
                  )}
                  <span className="font-medium text-slate-700 capitalize">
                    {levelName} Level Tables
                  </span>
                  <span className="text-sm text-slate-500">
                    ({tables.filter(t => selectedTables.has(t.id)).length}/{tables.length} selected)
                  </span>
                </div>
                <div className="flex gap-2" onClick={e => e.stopPropagation()}>
                  <button
                    onClick={() => selectAllInLevel(tables)}
                    className="text-xs text-emerald-600 hover:text-emerald-700"
                  >
                    All
                  </button>
                  <button
                    onClick={() => selectNoneInLevel(tables)}
                    className="text-xs text-slate-500 hover:text-slate-700"
                  >
                    None
                  </button>
                </div>
              </button>

              {/* Level Tables */}
              {expandedLevels.has(levelName) && (
                <div className="p-4 grid grid-cols-2 gap-3">
                  {tables.map((table) => {
                    const isSelected = selectedTables.has(table.id)
                    return (
                      <button
                        key={table.id}
                        onClick={() => toggleTable(table.id)}
                        className={`
                          flex items-start gap-3 p-3 rounded-lg border text-left transition-all
                          ${isSelected
                            ? 'border-emerald-500 bg-emerald-50 ring-1 ring-emerald-500'
                            : 'border-slate-200 bg-white hover:border-slate-300'
                          }
                        `}
                      >
                        <div className={`
                          w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 mt-0.5
                          ${isSelected ? 'border-emerald-500 bg-emerald-500' : 'border-slate-300'}
                        `}>
                          {isSelected && <Check className="w-3 h-3 text-white" />}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <Table className="w-4 h-4 text-slate-400" />
                            <span className="font-medium text-slate-900 truncate">
                              {table.label || table.id}
                            </span>
                          </div>
                          {table.description && (
                            <div className="mt-1 text-xs text-slate-500 truncate">
                              {table.description}
                            </div>
                          )}
                        </div>
                      </button>
                    )
                  })}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* File-based Table Selection (fallback when no profile) */}
      {!profileId && !isLoading && fileTables && (
        <div className="grid grid-cols-2 gap-3">
          {fileTables.map((table) => {
            const isSelected = selectedTables.has(table.name)
            return (
              <button
                key={table.name}
                onClick={() => toggleTable(table.name)}
                className={`
                  relative flex items-start gap-3 p-4 rounded-lg border text-left transition-all
                  ${isSelected
                    ? 'border-emerald-500 bg-emerald-50 ring-1 ring-emerald-500'
                    : 'border-slate-200 bg-white hover:border-slate-300'
                  }
                `}
              >
                <div className={`
                  w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 mt-0.5
                  ${isSelected ? 'border-emerald-500 bg-emerald-500' : 'border-slate-300'}
                `}>
                  {isSelected && <Check className="w-3 h-3 text-white" />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <Table className="w-4 h-4 text-slate-400" />
                    <span className="font-medium text-slate-900 truncate">{table.name}</span>
                  </div>
                  <div className="mt-1 text-sm text-slate-500">
                    {table.row_count?.toLocaleString() ?? '-'} rows × {table.column_count ?? '-'} cols
                  </div>
                  <div className="mt-1 text-xs text-slate-400 truncate">{table.file}</div>
                </div>
              </button>
            )
          })}
        </div>
      )}

      {isLoading && (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
        </div>
      )}

      {/* Context Options - Per DESIGN §9.1 */}
      <div className="bg-white rounded-lg border border-slate-200 p-4">
        <div className="flex items-center gap-2 mb-3">
          <Settings2 className="w-4 h-4 text-slate-500" />
          <label className="text-sm font-medium text-slate-700">Context Options</label>
        </div>
        <p className="text-xs text-slate-500 mb-4">
          Choose which context columns to include in your output tables.
        </p>
        <div className="space-y-3">
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={contextOptions.includeRunContext}
              onChange={(e) => setContextOptions(prev => ({
                ...prev,
                includeRunContext: e.target.checked,
              }))}
              className="mt-1 w-4 h-4 text-emerald-500 border-slate-300 rounded focus:ring-emerald-500"
            />
            <div>
              <div className="font-medium text-slate-900">Apply run-level context</div>
              <div className="text-sm text-slate-500">
                Add columns like LotID, WaferID, RecipeName to all output tables
              </div>
            </div>
          </label>
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={contextOptions.includeImageContext}
              onChange={(e) => setContextOptions(prev => ({
                ...prev,
                includeImageContext: e.target.checked,
              }))}
              className="mt-1 w-4 h-4 text-emerald-500 border-slate-300 rounded focus:ring-emerald-500"
            />
            <div>
              <div className="font-medium text-slate-900">Apply image-level context</div>
              <div className="text-sm text-slate-500">
                Add columns like ImageName, AcquisitionTime to image-level tables
              </div>
            </div>
          </label>
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-3">
        <button
          onClick={() => lockMutation.mutate()}
          disabled={selectedTables.size === 0 || lockMutation.isPending}
          className="px-6 py-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
        >
          {lockMutation.isPending ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            `Continue with ${selectedTables.size} table${selectedTables.size !== 1 ? 's' : ''}`
          )}
        </button>
      </div>
    </div>
  )
}
