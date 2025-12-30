import { useState, useEffect } from 'react'
import { Edit, Copy, Link, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { MarkdownRenderer } from './MarkdownRenderer'
import { CodeRenderer } from './CodeRenderer'
import { ADRViewer } from './ADRViewer'
import { SpecViewer } from './SpecViewer'
import { PlanViewer } from './PlanViewer'
import type { ArtifactType } from './types'

const API_BASE = 'http://localhost:8000/api/devtools'

interface ArtifactReaderProps {
  artifactId: string
  artifactType: ArtifactType
  filePath: string
  onEdit?: () => void
  className?: string
}

export function ArtifactReader({ artifactId, artifactType, filePath, onEdit, className }: ArtifactReaderProps) {
  const [content, setContent] = useState<string | object | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchContent = async () => {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch(`${API_BASE}/artifacts/${artifactId}`)
        if (!res.ok) throw new Error('Failed to fetch artifact')
        const data = await res.json()
        setContent(data.content || data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }
    if (artifactId) fetchContent()
  }, [artifactId])

  const handleCopy = () => {
    navigator.clipboard.writeText(typeof content === 'string' ? content : JSON.stringify(content, null, 2))
  }

  const handleCopyLink = () => {
    navigator.clipboard.writeText(`${window.location.origin}/devtools/workflow/${artifactType}/${artifactId}`)
  }

  if (loading) {
    return <div className="flex items-center justify-center h-64"><Loader2 className="animate-spin" /></div>
  }

  if (error) {
    return <div className="p-4 text-red-400">{error}</div>
  }

  const renderContent = () => {
    const contentStr = typeof content === 'string' ? content : JSON.stringify(content, null, 2)
    
    if (artifactType === 'adr') {
      return <ADRViewer content={contentStr} />
    }
    if (artifactType === 'spec') {
      return <SpecViewer content={contentStr} />
    }
    if (artifactType === 'plan') {
      return <PlanViewer content={contentStr} />
    }
    if (artifactType === 'discussion') {
      return <MarkdownRenderer content={content as string} />
    }
    if (artifactType === 'contract') {
      return <CodeRenderer code={content as string} language="python" />
    }
    return <pre className="text-sm">{JSON.stringify(content, null, 2)}</pre>
  }

  return (
    <div className={cn('flex flex-col h-full', className)}>
      <div className="flex items-center justify-between p-3 border-b border-zinc-800">
        <div>
          <h2 className="font-medium">{artifactId}</h2>
          <p className="text-xs text-zinc-500">{filePath}</p>
        </div>
        <div className="flex items-center gap-1">
          <button onClick={handleCopy} className="p-2 hover:bg-zinc-800 rounded" title="Copy content">
            <Copy size={16} />
          </button>
          <button onClick={handleCopyLink} className="p-2 hover:bg-zinc-800 rounded" title="Copy link">
            <Link size={16} />
          </button>
          {onEdit && (
            <button onClick={onEdit} className="p-2 hover:bg-zinc-800 rounded" title="Edit">
              <Edit size={16} />
            </button>
          )}
        </div>
      </div>
      <div className="flex-1 overflow-auto p-4">
        {renderContent()}
      </div>
    </div>
  )
}
