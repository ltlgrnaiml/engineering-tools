import { useState, useEffect, useCallback } from 'react'
import { X, Save, Loader2 } from 'lucide-react'
import Editor from '@monaco-editor/react'
import { cn } from '@/lib/utils'
import { ADREditorForm } from './ADREditorForm'
import { SpecEditorForm } from './SpecEditorForm'
import { DiscussionEditorForm } from './DiscussionEditorForm'
import { PlanEditorForm } from './PlanEditorForm'
import type { ArtifactType } from './types'

const API_BASE = 'http://localhost:8000/api/devtools'

interface ArtifactEditorProps {
  artifactId: string
  artifactType: ArtifactType
  isOpen: boolean
  onClose: () => void
  onSave?: () => void
}

export function ArtifactEditor({ artifactId, artifactType, isOpen, onClose, onSave }: ArtifactEditorProps) {
  const [content, setContent] = useState<string>('')
  const [originalContent, setOriginalContent] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [dirty, setDirty] = useState(false)

  useEffect(() => {
    if (isOpen && artifactId) {
      setLoading(true)
      fetch(`${API_BASE}/artifacts/${artifactId}`)
        .then(res => res.json())
        .then(data => {
          const c = typeof data.content === 'string' ? data.content : JSON.stringify(data.content || data, null, 2)
          setContent(c)
          setOriginalContent(c)
          setDirty(false)
        })
        .finally(() => setLoading(false))
    }
  }, [isOpen, artifactId])

  useEffect(() => {
    setDirty(content !== originalContent)
  }, [content, originalContent])

  const handleSave = useCallback(async () => {
    setSaving(true)
    try {
      await fetch(`${API_BASE}/artifacts/${artifactId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content }),
      })
      setOriginalContent(content)
      setDirty(false)
      onSave?.()
    } finally {
      setSaving(false)
    }
  }, [artifactId, content, onSave])

  const handleClose = useCallback(() => {
    if (dirty) {
      if (!window.confirm('You have unsaved changes. Discard?')) return
    }
    onClose()
  }, [dirty, onClose])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 's') {
        e.preventDefault()
        handleSave()
      }
      if (e.key === 'Escape') {
        handleClose()
      }
    }
    if (isOpen) window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, handleSave, handleClose])

  const getLanguage = () => {
    if (artifactType === 'contract') return 'python'
    if (artifactType === 'adr' || artifactType === 'spec') return 'json'
    return 'markdown'
  }

  return (
    <div
      className={cn(
        'fixed top-0 right-0 h-full w-[600px] bg-zinc-900 border-l border-zinc-800 shadow-xl z-50',
        'transform transition-transform duration-200',
        isOpen ? 'translate-x-0' : 'translate-x-full'
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-zinc-800">
        <div className="flex items-center gap-2">
          <span className="font-medium">{artifactId}</span>
          {dirty && <span className="text-xs text-amber-400 ml-2">• Unsaved changes</span>}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleSave}
            disabled={saving || !dirty}
            className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded text-sm"
          >
            {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
            Save
          </button>
          <button onClick={handleClose} className="p-2 hover:bg-zinc-800 rounded" title="Close">
            <X size={16} />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="h-[calc(100%-56px)]">
        {loading ? (
          <div className="flex items-center justify-center h-full"><Loader2 className="animate-spin" /></div>
        ) : artifactType === 'adr' ? (
          <ADREditorForm content={content} onChange={setContent} />
        ) : artifactType === 'spec' ? (
          <SpecEditorForm content={content} onChange={setContent} />
        ) : artifactType === 'discussion' ? (
          <DiscussionEditorForm content={content} onChange={setContent} />
        ) : artifactType === 'plan' ? (
          <PlanEditorForm content={content} onChange={setContent} />
        ) : (
          <Editor
            height="100%"
            language={getLanguage()}
            value={content}
            onChange={(v) => setContent(v || '')}
            theme="vs-dark"
            options={{ minimap: { enabled: false }, fontSize: 13, wordWrap: 'on' }}
          />
        )}
      </div>
    </div>
  )
}
