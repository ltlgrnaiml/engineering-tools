import { useState, useMemo } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Upload, File, FolderOpen, Loader2, Check, Filter } from 'lucide-react'
import { useDebugFetch } from '../debug'

interface SelectionPanelProps {
  runId: string
}

interface ScannedFile {
  path: string
  name: string
  extension: string
}

export function SelectionPanel({ runId }: SelectionPanelProps) {
  const [scannedFiles, setScannedFiles] = useState<ScannedFile[]>([])
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set())
  const [folderPath, setFolderPath] = useState('')
  const [extensionFilter, setExtensionFilter] = useState<string>('all')
  const queryClient = useQueryClient()
  const debugFetch = useDebugFetch()

  // Get unique extensions from scanned files
  const availableExtensions = useMemo(() => {
    const exts = new Set(scannedFiles.map(f => f.extension))
    return Array.from(exts).filter(e => e).sort()
  }, [scannedFiles])

  // Filter files by extension
  const filteredFiles = useMemo(() => {
    if (extensionFilter === 'all') return scannedFiles
    return scannedFiles.filter(f => f.extension === extensionFilter)
  }, [scannedFiles, extensionFilter])

  // Count selected in current filter
  const selectedInFilter = useMemo(() => {
    return filteredFiles.filter(f => selectedFiles.has(f.path)).length
  }, [filteredFiles, selectedFiles])

  const scanMutation = useMutation({
    mutationFn: async (path: string) => {
      const response = await debugFetch(`/api/dat/runs/${runId}/stages/selection/scan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folder_path: path }),
      })
      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`Failed to scan folder: ${response.status} - ${errorText}`)
      }
      return response.json()
    },
    onSuccess: (data) => {
      // Parse file info from paths
      const files: ScannedFile[] = (data.files || []).map((filePath: string) => {
        const name = filePath.split(/[/\\]/).pop() || filePath
        const ext = name.includes('.') ? '.' + name.split('.').pop()?.toLowerCase() : ''
        return { path: filePath, name, extension: ext }
      })
      setScannedFiles(files)
      // Select all files by default
      setSelectedFiles(new Set(files.map(f => f.path)))
      setExtensionFilter('all')
    },
  })

  const discoveryMutation = useMutation({
    mutationFn: async (path: string) => {
      const response = await debugFetch(`/api/dat/runs/${runId}/stages/discovery/lock`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folder_path: path }),
      })
      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`Failed to lock discovery: ${response.status} - ${errorText}`)
      }
      return response.json()
    },
  })

  const lockMutation = useMutation({
    mutationFn: async () => {
      const filesToLock = Array.from(selectedFiles)
      const response = await debugFetch(`/api/dat/runs/${runId}/stages/selection/lock`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ selected_files: filesToLock }),
      })
      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`Failed to lock stage: ${response.status} - ${errorText}`)
      }
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

  const handleContinue = async () => {
    if (selectedFiles.size === 0) return
    
    try {
      // Per ADR-0004: Discovery must be locked before Selection
      await discoveryMutation.mutateAsync(folderPath)
      // After discovery succeeds, lock selection
      lockMutation.mutate()
    } catch (error) {
      console.error('Failed to lock discovery:', error)
    }
  }

  const toggleFile = (filePath: string) => {
    setSelectedFiles(prev => {
      const next = new Set(prev)
      if (next.has(filePath)) {
        next.delete(filePath)
      } else {
        next.add(filePath)
      }
      return next
    })
  }

  const selectAll = () => {
    setSelectedFiles(prev => {
      const next = new Set(prev)
      filteredFiles.forEach(f => next.add(f.path))
      return next
    })
  }

  const selectNone = () => {
    setSelectedFiles(prev => {
      const next = new Set(prev)
      filteredFiles.forEach(f => next.delete(f.path))
      return next
    })
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
            placeholder="C:\path\to\data\folder or /path/to/data/folder"
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

      {/* Scanned Files with Selection */}
      {scannedFiles.length > 0 && (
        <div className="bg-white rounded-lg border border-slate-200 p-4">
          {/* Filter and Selection Controls */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <h3 className="text-sm font-medium text-slate-700">
                Files Found ({scannedFiles.length})
              </h3>
              
              {/* Extension Filter */}
              {availableExtensions.length > 1 && (
                <div className="flex items-center gap-2">
                  <Filter className="w-4 h-4 text-slate-400" />
                  <select
                    value={extensionFilter}
                    onChange={(e) => setExtensionFilter(e.target.value)}
                    className="text-sm border border-slate-300 rounded px-2 py-1"
                  >
                    <option value="all">All types</option>
                    {availableExtensions.map(ext => (
                      <option key={ext} value={ext}>{ext}</option>
                    ))}
                  </select>
                </div>
              )}
            </div>
            
            {/* Select All / None */}
            <div className="flex items-center gap-3 text-sm">
              <span className="text-slate-500">
                {selectedInFilter} of {filteredFiles.length} selected
              </span>
              <button
                onClick={selectAll}
                className="text-emerald-600 hover:text-emerald-700 font-medium"
              >
                Select All
              </button>
              <span className="text-slate-300">|</span>
              <button
                onClick={selectNone}
                className="text-slate-600 hover:text-slate-700 font-medium"
              >
                Clear
              </button>
            </div>
          </div>

          {/* File List with Checkboxes */}
          <div className="space-y-1 max-h-64 overflow-y-auto border border-slate-200 rounded-lg">
            {filteredFiles.map((file) => {
              const isSelected = selectedFiles.has(file.path)
              return (
                <button
                  key={file.path}
                  onClick={() => toggleFile(file.path)}
                  className={`w-full flex items-center gap-3 px-3 py-2 text-left transition-colors ${
                    isSelected ? 'bg-emerald-50' : 'hover:bg-slate-50'
                  }`}
                >
                  {/* Checkbox */}
                  <div className={`w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 ${
                    isSelected ? 'border-emerald-500 bg-emerald-500' : 'border-slate-300'
                  }`}>
                    {isSelected && <Check className="w-3 h-3 text-white" />}
                  </div>
                  
                  {/* File Icon */}
                  <File className="w-4 h-4 text-slate-400 flex-shrink-0" />
                  
                  {/* File Info */}
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-slate-900 truncate">{file.name}</div>
                    <div className="text-xs text-slate-500 truncate">{file.path}</div>
                  </div>
                  
                  {/* Extension Badge */}
                  <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
                    {file.extension || 'unknown'}
                  </span>
                </button>
              )
            })}
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
      <div className="flex justify-between items-center">
        <div className="text-sm text-slate-600">
          {selectedFiles.size > 0 && (
            <span className="font-medium text-emerald-600">
              {selectedFiles.size} file{selectedFiles.size !== 1 ? 's' : ''} selected
            </span>
          )}
        </div>
        <button
          onClick={handleContinue}
          disabled={selectedFiles.size === 0 || lockMutation.isPending || discoveryMutation.isPending}
          className="px-6 py-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
        >
          {lockMutation.isPending || discoveryMutation.isPending ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            'Continue'
          )}
        </button>
      </div>
    </div>
  )
}
