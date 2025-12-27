import { useState, useEffect } from 'react'
import { Database, Plus, Link2, Layers } from 'lucide-react'
import { api } from '../lib/api'

interface DataFile {
  id: string
  filename: string
  row_count: number
  column_count: number
  columns: string[]
}

interface DataSourcesPanelProps {
  projectId: string
  onDataChanged?: () => void
}

export function DataSourcesPanel({ projectId, onDataChanged }: DataSourcesPanelProps) {
  const [files, setFiles] = useState<DataFile[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showJoinModal, setShowJoinModal] = useState(false)
  const [joinConfig, setJoinConfig] = useState({
    primaryFileId: '',
    secondaryFileId: '',
    joinType: 'left' as 'left' | 'right' | 'inner' | 'outer',
    primaryColumn: '',
    secondaryColumn: '',
    columnsToInclude: [] as string[],
  })

  const fetchFiles = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await api.getDataFiles(projectId)
      setFiles(result.files)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load files')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchFiles()
  }, [projectId])

  const handleJoin = async () => {
    try {
      await api.joinFiles(projectId, {
        primary_file_id: joinConfig.primaryFileId,
        secondary_file_id: joinConfig.secondaryFileId,
        join_type: joinConfig.joinType,
        primary_column: joinConfig.primaryColumn,
        secondary_column: joinConfig.secondaryColumn,
        columns_to_include: joinConfig.columnsToInclude,
      })
      setShowJoinModal(false)
      fetchFiles()
      onDataChanged?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Join failed')
    }
  }

  const handleConcat = async (fileIds: string[]) => {
    try {
      await api.concatFiles(projectId, { file_ids: fileIds })
      fetchFiles()
      onDataChanged?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Concatenation failed')
    }
  }

  const primaryFile = files[0]
  const secondaryFiles = files.slice(1)

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Database className="h-5 w-5 text-gray-600" />
          <span className="font-medium text-gray-900">Data Sources</span>
          <span className="text-sm text-gray-500">({files.length} files)</span>
        </div>
        <button
          onClick={() => setShowJoinModal(true)}
          disabled={files.length < 2}
          className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
          title="Join files"
        >
          <Plus className="h-4 w-4" />
          Add Join
        </button>
      </div>

      {loading ? (
        <div className="p-6 text-center text-gray-500">Loading files...</div>
      ) : error ? (
        <div className="p-6 text-center text-red-600">{error}</div>
      ) : files.length === 0 ? (
        <div className="p-6 text-center text-gray-500">No data files uploaded yet</div>
      ) : (
        <div className="p-4 space-y-3">
          {primaryFile && (
            <div className="border-2 border-blue-200 bg-blue-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Database className="h-5 w-5 text-blue-600" />
                  <div>
                    <div className="font-medium text-gray-900">{primaryFile.filename}</div>
                    <div className="text-sm text-gray-500">
                      {primaryFile.row_count.toLocaleString()} rows, {primaryFile.column_count} columns
                    </div>
                  </div>
                </div>
                <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded">
                  Primary
                </span>
              </div>
            </div>
          )}

          {secondaryFiles.map((file) => (
            <div key={file.id} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Layers className="h-5 w-5 text-gray-400" />
                  <div>
                    <div className="font-medium text-gray-900">{file.filename}</div>
                    <div className="text-sm text-gray-500">
                      {file.row_count.toLocaleString()} rows, {file.column_count} columns
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => {
                      setJoinConfig({
                        ...joinConfig,
                        primaryFileId: primaryFile?.id || '',
                        secondaryFileId: file.id,
                      })
                      setShowJoinModal(true)
                    }}
                    className="p-1 text-blue-600 hover:bg-blue-50 rounded"
                    title="Join with primary"
                  >
                    <Link2 className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => handleConcat([primaryFile?.id || '', file.id])}
                    className="p-1 text-green-600 hover:bg-green-50 rounded"
                    title="Concatenate with primary"
                  >
                    <Layers className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {showJoinModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Configure Join</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Join Type</label>
                <select
                  value={joinConfig.joinType}
                  onChange={(e) => setJoinConfig({ ...joinConfig, joinType: e.target.value as 'left' | 'right' | 'inner' | 'outer' })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                >
                  <option value="left">Left Join</option>
                  <option value="right">Right Join</option>
                  <option value="inner">Inner Join</option>
                  <option value="outer">Outer Join</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Primary Column</label>
                <select
                  value={joinConfig.primaryColumn}
                  onChange={(e) => setJoinConfig({ ...joinConfig, primaryColumn: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                >
                  <option value="">Select column...</option>
                  {primaryFile?.columns.map((col) => (
                    <option key={col} value={col}>{col}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Secondary Column</label>
                <select
                  value={joinConfig.secondaryColumn}
                  onChange={(e) => setJoinConfig({ ...joinConfig, secondaryColumn: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                >
                  <option value="">Select column...</option>
                  {files.find(f => f.id === joinConfig.secondaryFileId)?.columns.map((col) => (
                    <option key={col} value={col}>{col}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowJoinModal(false)}
                className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleJoin}
                disabled={!joinConfig.primaryColumn || !joinConfig.secondaryColumn}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                Join Files
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
