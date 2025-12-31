import { useState, useEffect } from 'react'
import { Edit, Copy, Link, Loader2, Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'
import { MarkdownRenderer } from './MarkdownRenderer'
import { CodeRenderer } from './CodeRenderer'
import { SchemaInterpreter } from './SchemaInterpreter'
import { usePrompt } from '@/hooks/useWorkflowApi'
import type { ArtifactType, FileFormat } from './types'

const API_BASE = 'http://localhost:8000/api/devtools'

interface ArtifactReaderProps {
  artifactId: string
  artifactType: ArtifactType
  fileFormat?: FileFormat
  filePath: string
  onEdit?: () => void
  className?: string
}

export function ArtifactReader({ artifactId, artifactType, fileFormat: propFileFormat, filePath, onEdit, className }: ArtifactReaderProps) {
  const [content, setContent] = useState<string | object | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [fileFormat, setFileFormat] = useState<FileFormat>(propFileFormat || 'unknown')
  const [promptCopied, setPromptCopied] = useState(false)
  const { fetchPrompt, loading: promptLoading } = usePrompt()

  useEffect(() => {
    const fetchContent = async () => {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch(`${API_BASE}/artifacts/${artifactId}`)
        if (!res.ok) throw new Error('Failed to fetch artifact')
        const data = await res.json()
        setContent(data.content || data)
        // Update file format from API response if available
        if (data.file_format) {
          setFileFormat(data.file_format)
        } else if (data.file_path) {
          // Fallback: detect from file extension
          const ext = data.file_path.split('.').pop()?.toLowerCase()
          if (ext === 'json') setFileFormat('json')
          else if (ext === 'md') setFileFormat('markdown')
          else if (ext === 'py') setFileFormat('python')
        }
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

  const handleCopyPrompt = async () => {
    try {
      // Default to creating the next logical artifact type
      const targetTypeMap: Record<ArtifactType, ArtifactType> = {
        discussion: 'adr',
        adr: 'spec',
        spec: 'plan',
        plan: 'contract',
        contract: 'plan',
      }
      const targetType = targetTypeMap[artifactType] || 'adr'
      const response = await fetchPrompt(artifactId, targetType)
      await navigator.clipboard.writeText(response.prompt)
      setPromptCopied(true)
      setTimeout(() => setPromptCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy prompt:', err)
    }
  }

  if (loading) {
    return <div className="flex items-center justify-center h-64"><Loader2 className="animate-spin" /></div>
  }

  if (error) {
    return <div className="p-4 text-red-400">{error}</div>
  }

  const renderContent = () => {
    try {
      // Route based on file format - schema-driven, no hardcoded interfaces
      if (fileFormat === 'markdown') {
        const contentStr = typeof content === 'string' ? content : JSON.stringify(content, null, 2)
        return <MarkdownRenderer content={contentStr} />
      }
      
      // Python files use CodeRenderer
      if (fileFormat === 'python' || artifactType === 'contract') {
        const contentStr = typeof content === 'string' ? content : JSON.stringify(content, null, 2)
        return <CodeRenderer code={contentStr} language="python" />
      }
      
      // JSON files use SchemaInterpreter - renders UI from JSON Schema
      if (fileFormat === 'json' || fileFormat === 'unknown') {
        const data = typeof content === 'string' ? JSON.parse(content) : content
        // Map artifact type to schema type
        const schemaType = artifactType === 'adr' ? 'adr' 
          : artifactType === 'spec' ? 'spec'
          : artifactType === 'plan' ? 'plan'
          : 'adr' // fallback
        return <SchemaInterpreter schemaType={schemaType} data={data as Record<string, unknown>} />
      }
      
      // Fallback: show raw content
      const contentStr = typeof content === 'string' ? content : JSON.stringify(content, null, 2)
      return <pre className="text-sm whitespace-pre-wrap">{contentStr}</pre>
    } catch (err) {
      return <div className="p-4 text-red-400">Error rendering content: {err instanceof Error ? err.message : 'Unknown error'}</div>
    }
  }

  return (
    <div className={cn('flex flex-col h-full', className)}>
      <div className="flex items-center justify-between p-3 border-b border-zinc-800">
        <div>
          <h2 className="font-medium">{artifactId}</h2>
          <p className="text-xs text-zinc-500">{filePath}</p>
        </div>
        <div className="flex items-center gap-1">
          <button 
            onClick={handleCopyPrompt} 
            disabled={promptLoading}
            className="flex items-center gap-1 px-2 py-1 text-xs bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 rounded border border-purple-500/30" 
            title="Copy AI prompt for next artifact"
          >
            <Sparkles size={14} />
            {promptCopied ? 'Copied!' : promptLoading ? 'Loading...' : 'Copy AI Prompt'}
          </button>
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
