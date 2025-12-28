import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Table, Check, Loader2 } from 'lucide-react'
import { useDebugFetch } from '../debug'

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
  const queryClient = useQueryClient()
  const debugFetch = useDebugFetch()

  const { data: tables, isLoading } = useQuery({
    queryKey: ['dat-available-tables', runId],
    queryFn: async (): Promise<TableInfo[]> => {
      const response = await debugFetch(`/api/dat/v1/runs/${runId}/stages/table_selection/tables`)
      if (!response.ok) throw new Error('Failed to fetch tables')
      return response.json()
    },
  })

  const lockMutation = useMutation({
    mutationFn: async () => {
      // Group selected tables by file path for backend schema compatibility
      const selectedTablesByFile: Record<string, string[]> = {}
      
      // Find selected tables and group them by file
      Array.from(selectedTables).forEach(tableName => {
        const tableInfo = tables?.find(t => t.name === tableName)
        if (tableInfo) {
          if (!selectedTablesByFile[tableInfo.file]) {
            selectedTablesByFile[tableInfo.file] = []
          }
          selectedTablesByFile[tableInfo.file].push(tableName)
        }
      })
      
      const response = await debugFetch(`/api/dat/v1/runs/${runId}/stages/table_selection/lock`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ selected_tables: selectedTablesByFile }),
      })
      if (!response.ok) throw new Error('Failed to lock stage')
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dat-run', runId] })
    },
  })

  const toggleTable = (tableName: string) => {
    setSelectedTables(prev => {
      const newSet = new Set(prev)
      if (newSet.has(tableName)) {
        newSet.delete(tableName)
      } else {
        newSet.add(tableName)
      }
      return newSet
    })
  }

  const selectAll = () => {
    setSelectedTables(new Set(tables?.map(t => t.name) || []))
  }

  const selectNone = () => {
    setSelectedTables(new Set())
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Table Selection</h2>
        <p className="text-slate-600 mt-1">Choose which tables to include in the aggregation.</p>
      </div>

      {/* Selection Controls */}
      <div className="flex items-center gap-4">
        <span className="text-sm text-slate-600">
          {selectedTables.size} of {tables?.length || 0} tables selected
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

      {/* Table Grid */}
      {isLoading ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3">
          {tables?.map((table) => {
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
                    {table.row_count.toLocaleString()} rows × {table.column_count} cols
                  </div>
                  <div className="mt-1 text-xs text-slate-400 truncate">{table.file}</div>
                </div>
              </button>
            )
          })}
        </div>
      )}

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
