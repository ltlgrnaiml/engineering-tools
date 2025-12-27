import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  FileJson,
  Settings,
  ChevronLeft,
  ChevronRight,
  Maximize2,
  Minimize2,
  RefreshCw,
  Search,
  X,
  ChevronDown,
  ChevronUp,
  Folder,
  Plus,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { ADRFormEditor } from '@/components/ADRFormEditor'

interface ADRSummary {
  id: string
  title: string
  status: string
  date: string
  scope: string
  filename: string
  folder: string
}

interface ADRContent {
  filename: string
  content: Record<string, unknown>
  raw_json: string
}

interface ValidationResult {
  valid: boolean
  errors: string[]
  warnings: string[]
}

const API_BASE = 'http://localhost:8000/api/v1/devtools'

export function DevToolsPage() {
  const [adrs, setAdrs] = useState<ADRSummary[]>([])
  const [selectedAdr, setSelectedAdr] = useState<ADRContent | null>(null)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [activeTab, setActiveTab] = useState<'reader' | 'editor'>('reader')
  const [isLoading, setIsLoading] = useState(true)
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set(['core', 'shared', 'dat', 'pptx', 'sov', 'devtools']))
  const [isCreatingNew, setIsCreatingNew] = useState(false)
  const [createFolder, setCreateFolder] = useState('core')

  useEffect(() => {
    fetchAdrs()
  }, [])

  const fetchAdrs = async () => {
    setIsLoading(true)
    try {
      const response = await fetch(`${API_BASE}/adrs`)
      if (response.ok) {
        const data = await response.json()
        setAdrs(data)
      }
    } catch (error) {
      console.error('Failed to fetch ADRs:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const selectAdr = async (folder: string, filename: string) => {
    try {
      const response = await fetch(`${API_BASE}/adrs/${folder}/${filename}`)
      if (response.ok) {
        const data = await response.json()
        setSelectedAdr(data)
        setIsCreatingNew(false)
      }
    } catch (error) {
      console.error('Failed to fetch ADR:', error)
    }
  }

  const toggleFolder = (folder: string) => {
    setExpandedFolders((prev) => {
      const next = new Set(prev)
      if (next.has(folder)) {
        next.delete(folder)
      } else {
        next.add(folder)
      }
      return next
    })
  }


  const handleFormSave = async (data: Record<string, any>) => {
    try {
      if (isCreatingNew) {
        // Create new ADR
        const response = await fetch(`${API_BASE}/adrs`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            folder: createFolder,
            adr_data: data,
          }),
        })
        if (response.ok) {
          setIsCreatingNew(false)
          fetchAdrs()
        }
      } else if (selectedAdr) {
        // Update existing ADR via form
        const adr = adrs.find(a => a.filename === selectedAdr.filename)
        const folder = adr?.folder || 'root'
        
        const response = await fetch(`${API_BASE}/adrs/${folder}/${selectedAdr.filename}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ content: data }),
        })
        if (response.ok) {
          const updated = await response.json()
          setSelectedAdr(updated)
          fetchAdrs()
        }
      }
    } catch (error) {
      console.error('Failed to save:', error)
    }
  }

  const startCreateNew = () => {
    setIsCreatingNew(true)
    setSelectedAdr(null)
    setActiveTab('editor')
  }


  const filteredAdrs = adrs.filter(
    (adr) =>
      adr.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      adr.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      adr.scope.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'accepted':
        return 'bg-green-100 text-green-800'
      case 'proposed':
        return 'bg-blue-100 text-blue-800'
      case 'deprecated':
        return 'bg-yellow-100 text-yellow-800'
      case 'superseded':
        return 'bg-gray-100 text-gray-800'
      default:
        return 'bg-slate-100 text-slate-800'
    }
  }

  const renderReaderContent = () => {
    if (!selectedAdr) {
      return (
        <div className="flex items-center justify-center h-full text-slate-400">
          <div className="text-center">
            <FileJson className="w-12 h-12 mx-auto mb-4" />
            <p>Select an ADR to view</p>
          </div>
        </div>
      )
    }

    const content = selectedAdr.content as Record<string, unknown>

    return (
      <div className="p-6 overflow-auto h-full">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Header */}
          <div className="border-b border-slate-200 pb-4">
            <div className="flex items-center gap-2 mb-2">
              <span className={cn('px-2 py-1 rounded-full text-xs font-medium', getStatusColor(content.status as string))}>
                {(content.status as string)?.toUpperCase()}
              </span>
              <span className="text-xs text-slate-500">{content.scope as string}</span>
            </div>
            <h1 className="text-2xl font-bold text-slate-900">{content.title as string}</h1>
            <p className="text-sm text-slate-500 mt-1">
              {content.id as string} • {content.date as string}
            </p>
          </div>

          {/* Context */}
          <section>
            <h2 className="text-lg font-semibold text-slate-900 mb-2">Context</h2>
            <p className="text-slate-700 leading-relaxed">{String(content.context || '')}</p>
          </section>

          {/* Decision */}
          <section>
            <h2 className="text-lg font-semibold text-slate-900 mb-2">Decision</h2>
            <p className="text-slate-700 leading-relaxed">{String(content.decision_primary || '')}</p>
          </section>

          {/* Decision Details */}
          {content.decision_details && typeof content.decision_details === 'object' && (
            <section>
              <h2 className="text-lg font-semibold text-slate-900 mb-2">Details</h2>
              <div className="bg-slate-50 rounded-lg p-4">
                {(content.decision_details as Record<string, unknown>).constraints && (
                  <div className="mb-4">
                    <h3 className="font-medium text-slate-800 mb-2">Constraints</h3>
                    <ul className="list-disc list-inside space-y-1 text-sm text-slate-700">
                      {((content.decision_details as Record<string, unknown>).constraints as string[]).map((c, i) => (
                        <li key={i}>{c}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </section>
          )}

          {/* Consequences */}
          {Array.isArray(content.consequences) && content.consequences.length > 0 && (
            <section>
              <h2 className="text-lg font-semibold text-slate-900 mb-2">Consequences</h2>
              <ul className="list-disc list-inside space-y-1 text-slate-700">
                {(content.consequences as string[]).map((c, i) => (
                  <li key={i}>{c}</li>
                ))}
              </ul>
            </section>
          )}

          {/* Guardrails */}
          {Array.isArray(content.guardrails) && content.guardrails.length > 0 && (
            <section>
              <h2 className="text-lg font-semibold text-slate-900 mb-2">Guardrails</h2>
              <div className="space-y-3">
                {(content.guardrails as Array<Record<string, unknown>>).map((g, i) => (
                  <div key={i} className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                    <p className="font-medium text-amber-900">{g.rule as string}</p>
                    <p className="text-sm text-amber-700 mt-1">
                      <span className="font-medium">Enforcement:</span> {g.enforcement as string}
                    </p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Tags */}
          {Array.isArray(content.tags) && content.tags.length > 0 && (
            <section>
              <h2 className="text-lg font-semibold text-slate-900 mb-2">Tags</h2>
              <div className="flex flex-wrap gap-2">
                {(content.tags as string[]).map((tag, i) => (
                  <span key={i} className="px-2 py-1 bg-slate-100 rounded text-sm text-slate-700">
                    {tag}
                  </span>
                ))}
              </div>
            </section>
          )}
        </div>
      </div>
    )
  }

  const renderEditorContent = () => {
    if (isCreatingNew) {
      return (
        <div className="h-full flex flex-col">
          <div className="p-3 border-b border-slate-200 bg-slate-50">
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Select Folder for New ADR
            </label>
            <select
              value={createFolder}
              onChange={(e) => setCreateFolder(e.target.value)}
              className="w-full max-w-xs px-3 py-2 border border-slate-300 rounded-md text-sm"
            >
              <option value="core">Core Platform</option>
              <option value="shared">Shared / Cross-Tool</option>
              <option value="dat">Data Aggregator (DAT)</option>
              <option value="pptx">PPTX Generator</option>
              <option value="sov">SOV Analyzer</option>
              <option value="devtools">DevTools</option>
            </select>
          </div>
          <div className="flex-1 overflow-hidden">
            <ADRFormEditor
              adr={null}
              isNewAdr={true}
              onSave={handleFormSave}
            />
          </div>
        </div>
      )
    }

    if (!selectedAdr) {
      return (
        <div className="flex items-center justify-center h-full text-slate-400">
          <div className="text-center">
            <FileJson className="w-12 h-12 mx-auto mb-4" />
            <p>Select an ADR to edit</p>
          </div>
        </div>
      )
    }

    return (
      <div className="h-full">
        <ADRFormEditor
          adr={selectedAdr.content as Record<string, any>}
          isNewAdr={false}
          onSave={handleFormSave}
        />
      </div>
    )
  }

  // Fullscreen mode
  if (isFullscreen) {
    return (
      <div className="fixed inset-0 z-50 bg-white">
        <div className="h-full flex flex-col">
          <div className="flex items-center justify-between p-4 border-b border-slate-200 bg-slate-50">
            <h2 className="font-semibold text-slate-900">
              {selectedAdr?.content?.title as string || 'ADR Reader'}
            </h2>
            <button
              onClick={() => setIsFullscreen(false)}
              className="p-2 hover:bg-slate-200 rounded-md"
            >
              <Minimize2 className="w-5 h-5" />
            </button>
          </div>
          <div className="flex-1 overflow-auto">{renderReaderContent()}</div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-40">
        <div className="max-w-full mx-auto px-4">
          <div className="flex items-center justify-between h-14">
            <div className="flex items-center gap-4">
              <Link to="/" className="flex items-center gap-2 text-slate-600 hover:text-slate-900">
                <ChevronLeft className="w-4 h-4" />
                Back to Home
              </Link>
              <div className="flex items-center gap-2">
                <Settings className="w-5 h-5 text-cyan-600" />
                <span className="font-semibold text-slate-900">DevTools</span>
                <span className="px-2 py-0.5 bg-cyan-100 text-cyan-800 text-xs rounded-full">Developer Mode</span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={startCreateNew}
                className="flex items-center gap-1 px-3 py-1.5 bg-cyan-600 text-white rounded-md text-sm font-medium hover:bg-cyan-700"
                title="Create New ADR"
              >
                <Plus className="w-4 h-4" />
                New ADR
              </button>
              <button
                onClick={fetchAdrs}
                className="p-2 hover:bg-slate-100 rounded-md"
                title="Refresh"
                aria-label="Refresh ADR list"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="flex h-[calc(100vh-56px)]">
        {/* Sidebar - ADR List */}
        <div
          className={cn(
            'bg-white border-r border-slate-200 flex flex-col transition-all duration-200',
            sidebarCollapsed ? 'w-12' : 'w-80'
          )}
        >
          <div className="flex items-center justify-between p-3 border-b border-slate-200">
            {!sidebarCollapsed && (
              <div className="flex items-center gap-2 flex-1">
                <Search className="w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search ADRs..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="flex-1 text-sm bg-transparent focus:outline-none"
                />
                {searchQuery && (
                  <button onClick={() => setSearchQuery('')} className="text-slate-400 hover:text-slate-600">
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            )}
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="p-1 hover:bg-slate-100 rounded"
              title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
              aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              {sidebarCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
            </button>
          </div>

          {!sidebarCollapsed && (
            <div className="flex-1 overflow-auto">
              {isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <RefreshCw className="w-5 h-5 animate-spin text-slate-400" />
                </div>
              ) : (
                <div className="p-2 space-y-2">
                  {(() => {
                    // Group ADRs by folder
                    const folderGroups = filteredAdrs.reduce((acc, adr) => {
                      const folder = adr.folder || 'root'
                      if (!acc[folder]) acc[folder] = []
                      acc[folder].push(adr)
                      return acc
                    }, {} as Record<string, ADRSummary[]>)

                    const folderLabels: Record<string, string> = {
                      core: 'Core Platform',
                      shared: 'Shared / Cross-Tool',
                      dat: 'Data Aggregator (DAT)',
                      pptx: 'PPTX Generator',
                      sov: 'SOV Analyzer',
                      devtools: 'DevTools',
                      root: 'Uncategorized',
                    }

                    return Object.entries(folderGroups)
                      .sort(([a], [b]) => {
                        const order = ['core', 'shared', 'dat', 'pptx', 'sov', 'devtools', 'root']
                        return order.indexOf(a) - order.indexOf(b)
                      })
                      .map(([folder, adrsInFolder]) => (
                        <div key={folder} className="space-y-1">
                          <button
                            onClick={() => toggleFolder(folder)}
                            className="w-full flex items-center gap-2 px-2 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 rounded-md"
                          >
                            <Folder className="w-4 h-4 text-slate-500" />
                            <span className="flex-1 text-left">{folderLabels[folder] || folder}</span>
                            <span className="text-xs text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded-full">
                              {adrsInFolder.length}
                            </span>
                            {expandedFolders.has(folder) ? (
                              <ChevronUp className="w-4 h-4 text-slate-400" />
                            ) : (
                              <ChevronDown className="w-4 h-4 text-slate-400" />
                            )}
                          </button>
                          {expandedFolders.has(folder) && (
                            <div className="ml-2 pl-3 border-l-2 border-slate-200 space-y-1">
                              {adrsInFolder.map((adr) => (
                                <button
                                  key={`${folder}/${adr.filename}`}
                                  onClick={() => selectAdr(adr.folder, adr.filename)}
                                  className={cn(
                                    'w-full text-left p-2 rounded-md transition-colors',
                                    selectedAdr?.filename === adr.filename
                                      ? 'bg-primary-50 border border-primary-200'
                                      : 'hover:bg-slate-50'
                                  )}
                                >
                                  <div className="flex items-start gap-2">
                                    <FileJson className="w-4 h-4 mt-0.5 text-slate-400 flex-shrink-0" />
                                    <div className="flex-1 min-w-0">
                                      <p className="text-sm font-medium text-slate-900 truncate">{adr.title}</p>
                                      <div className="flex items-center gap-2 mt-1">
                                        <span
                                          className={cn(
                                            'px-1.5 py-0.5 rounded text-xs font-medium',
                                            getStatusColor(adr.status)
                                          )}
                                        >
                                          {adr.status}
                                        </span>
                                        <span className="text-xs text-slate-500 truncate">{adr.id}</span>
                                      </div>
                                    </div>
                                  </div>
                                </button>
                              ))}
                            </div>
                          )}
                        </div>
                      ))
                  })()}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Main Content - Split View */}
        <div className="flex-1 flex flex-col">
          {/* Tab Bar */}
          <div className="flex items-center justify-between px-4 py-2 border-b border-slate-200 bg-white">
            <div className="flex items-center gap-1">
              <button
                onClick={() => setActiveTab('reader')}
                className={cn(
                  'px-3 py-1.5 rounded-md text-sm font-medium transition-colors',
                  activeTab === 'reader' ? 'bg-primary-100 text-primary-700' : 'text-slate-600 hover:bg-slate-100'
                )}
              >
                Reader
              </button>
              <button
                onClick={() => setActiveTab('editor')}
                className={cn(
                  'px-3 py-1.5 rounded-md text-sm font-medium transition-colors',
                  activeTab === 'editor' ? 'bg-primary-100 text-primary-700' : 'text-slate-600 hover:bg-slate-100'
                )}
              >
                Editor
              </button>
            </div>
            <div className="flex items-center gap-2">
              {activeTab === 'reader' && (
                <button
                  onClick={() => setIsFullscreen(true)}
                  className="p-1.5 hover:bg-slate-100 rounded-md"
                  title="Fullscreen"
                  aria-label="Enter fullscreen mode"
                >
                  <Maximize2 className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>

          {/* Content Area */}
          <div className="flex-1 flex overflow-hidden">
            {/* Split view - Reader on left, Editor on right (in split mode) */}
            <div className={cn('flex-1 overflow-auto bg-white', activeTab !== 'reader' && 'hidden')}>
              {renderReaderContent()}
            </div>
            <div className={cn('flex-1 overflow-hidden border-l border-slate-200', activeTab !== 'editor' && 'hidden')}>
              {renderEditorContent()}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
