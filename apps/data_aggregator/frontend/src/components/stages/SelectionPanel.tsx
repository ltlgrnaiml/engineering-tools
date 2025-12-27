import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Upload, File, X, FolderOpen, Loader2 } from 'lucide-react'

interface SelectionPanelProps {
  runId: string
}

export function SelectionPanel({ runId }: SelectionPanelProps) {
  const [selectedFiles, setSelectedFiles] = useState<string[]>([])
  const [folderPath, setFolderPath] = useState('')
  const queryClient = useQueryClient()

  const scanMutation = useMutation({
    mutationFn: async (path: string) => {
      const response = await fetch(`/api/dat/runs/${runId}/stages/selection/scan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folder_path: path }),
      })
      if (!response.ok) throw new Error('Failed to scan folder')
      return response.json()
    },
    onSuccess: (data) => {
      setSelectedFiles(data.files || [])
    },
  })

  const lockMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch(`/api/dat/runs/${runId}/stages/selection/lock`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ selected_files: selectedFiles }),
      })
      if (!response.ok) throw new Error('Failed to lock stage')
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dat-run', runId] })
    },
  })

  const handleScan = () => {
    if (folderPath.trim()) {
      scanMutation.mutate(folderPath)
    }
  }

  const handleRemoveFile = (file: string) => {
    setSelectedFiles(prev => prev.filter(f => f !== file))
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">File Selection</h2>
        <p className="text-slate-600 mt-1">Select the files or folder containing data to aggregate.</p>
      </div>

      {/* Folder Path Input */}
      <div className="bg-white rounded-lg border border-slate-200 p-4">
        <label className="block text-sm font-medium text-slate-700 mb-2">
          <FolderOpen className="w-4 h-4 inline mr-1" />
          Folder Path
        </label>
        <div className="flex gap-2">
          <input
            type="text"
            value={folderPath}
            onChange={(e) => setFolderPath(e.target.value)}
            placeholder="/path/to/data/folder"
            className="flex-1 px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
          />
          <button
            onClick={handleScan}
            disabled={!folderPath.trim() || scanMutation.isPending}
            className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg font-medium transition-colors disabled:opacity-50"
          >
            {scanMutation.isPending ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              'Scan'
            )}
          </button>
        </div>
      </div>

      {/* Selected Files */}
      {selectedFiles.length > 0 && (
        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <h3 className="text-sm font-medium text-slate-700 mb-3">
            Selected Files ({selectedFiles.length})
          </h3>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {selectedFiles.map((file) => (
              <div
                key={file}
                className="flex items-center justify-between px-3 py-2 bg-slate-50 rounded-lg"
              >
                <div className="flex items-center gap-2">
                  <File className="w-4 h-4 text-slate-400" />
                  <span className="text-sm text-slate-700 truncate">{file}</span>
                </div>
                <button
                  onClick={() => handleRemoveFile(file)}
                  className="p-1 hover:bg-slate-200 rounded"
                >
                  <X className="w-4 h-4 text-slate-400" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Drop Zone */}
      <div className="border-2 border-dashed border-slate-300 rounded-lg p-8 text-center hover:border-emerald-400 transition-colors">
        <Upload className="w-10 h-10 mx-auto mb-3 text-slate-400" />
        <p className="text-slate-600">Drag and drop files here, or</p>
        <button className="mt-2 text-emerald-600 hover:text-emerald-700 font-medium">
          Browse files
        </button>
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-3">
        <button
          onClick={() => lockMutation.mutate()}
          disabled={selectedFiles.length === 0 || lockMutation.isPending}
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
