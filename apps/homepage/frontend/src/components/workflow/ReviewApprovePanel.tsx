import { useState } from 'react'
import { Check, X, Edit, Eye, CheckCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ArtifactType, ArtifactStatus } from './types'

interface GeneratedArtifact {
  id: string
  type: ArtifactType
  title: string
  status: ArtifactStatus
  content?: string
  approved?: boolean
  rejected?: boolean
}

interface ReviewApprovePanelProps {
  artifacts: GeneratedArtifact[]
  onApprove: (artifactId: string) => void
  onReject: (artifactId: string) => void
  onEdit: (artifactId: string) => void
  onApproveAll: () => void
  onComplete: () => void
  className?: string
}

const TYPE_LABELS: Record<ArtifactType, string> = {
  discussion: 'Discussion',
  adr: 'ADR',
  spec: 'SPEC',
  plan: 'Plan',
  contract: 'Contract',
}

const TYPE_COLORS: Record<ArtifactType, string> = {
  discussion: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
  adr: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  spec: 'bg-green-500/20 text-green-300 border-green-500/30',
  plan: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
  contract: 'bg-pink-500/20 text-pink-300 border-pink-500/30',
}

export function ReviewApprovePanel({
  artifacts,
  onApprove,
  onReject,
  onEdit,
  onApproveAll,
  onComplete,
  className,
}: ReviewApprovePanelProps) {
  const [selectedArtifact, setSelectedArtifact] = useState<string | null>(null)

  const pendingCount = artifacts.filter(a => !a.approved && !a.rejected).length
  const approvedCount = artifacts.filter(a => a.approved).length
  const allReviewed = pendingCount === 0

  return (
    <div className={cn('flex flex-col h-full bg-zinc-900', className)}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-zinc-800">
        <div>
          <h2 className="text-lg font-semibold">Review Generated Artifacts</h2>
          <p className="text-sm text-zinc-500">
            {approvedCount} approved, {pendingCount} pending review
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onApproveAll}
            disabled={allReviewed}
            className="flex items-center gap-1 px-3 py-1.5 text-sm bg-green-600/20 hover:bg-green-600/30 text-green-300 rounded border border-green-500/30 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <CheckCircle size={14} />
            Approve All
          </button>
        </div>
      </div>

      {/* Artifact List */}
      <div className="flex-1 overflow-y-auto">
        {artifacts.map((artifact) => (
          <div
            key={artifact.id}
            className={cn(
              'border-b border-zinc-800 transition-colors',
              selectedArtifact === artifact.id && 'bg-zinc-800/50',
              artifact.approved && 'bg-green-500/5',
              artifact.rejected && 'bg-red-500/5 opacity-50'
            )}
          >
            <div className="flex items-center gap-3 p-3">
              {/* Status indicator */}
              <div className={cn(
                'w-8 h-8 rounded-full flex items-center justify-center',
                artifact.approved ? 'bg-green-500' : artifact.rejected ? 'bg-red-500' : 'bg-zinc-700'
              )}>
                {artifact.approved ? (
                  <Check size={16} />
                ) : artifact.rejected ? (
                  <X size={16} />
                ) : (
                  <span className="text-xs">{artifacts.indexOf(artifact) + 1}</span>
                )}
              </div>

              {/* Artifact info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className={cn(
                    'px-2 py-0.5 text-xs rounded border',
                    TYPE_COLORS[artifact.type]
                  )}>
                    {TYPE_LABELS[artifact.type]}
                  </span>
                  <span className="font-medium truncate">{artifact.id}</span>
                </div>
                <p className="text-sm text-zinc-500 truncate">{artifact.title}</p>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setSelectedArtifact(selectedArtifact === artifact.id ? null : artifact.id)}
                  className="p-2 hover:bg-zinc-700 rounded"
                  title="Preview"
                >
                  <Eye size={16} />
                </button>
                <button
                  onClick={() => onEdit(artifact.id)}
                  className="p-2 hover:bg-zinc-700 rounded"
                  title="Edit"
                >
                  <Edit size={16} />
                </button>
                {!artifact.approved && !artifact.rejected && (
                  <>
                    <button
                      onClick={() => onApprove(artifact.id)}
                      className="p-2 hover:bg-green-600/20 text-green-400 rounded"
                      title="Approve"
                    >
                      <Check size={16} />
                    </button>
                    <button
                      onClick={() => onReject(artifact.id)}
                      className="p-2 hover:bg-red-600/20 text-red-400 rounded"
                      title="Reject"
                    >
                      <X size={16} />
                    </button>
                  </>
                )}
              </div>
            </div>

            {/* Preview panel */}
            {selectedArtifact === artifact.id && artifact.content && (
              <div className="px-3 pb-3">
                <div className="p-3 bg-zinc-950 rounded border border-zinc-800">
                  <pre className="text-sm text-zinc-300 whitespace-pre-wrap overflow-auto max-h-48">
                    {artifact.content}
                  </pre>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="flex justify-end gap-2 p-4 border-t border-zinc-800">
        <button
          onClick={onComplete}
          disabled={!allReviewed}
          className="flex items-center gap-2 px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed rounded"
        >
          <CheckCircle size={16} />
          Complete Review
        </button>
      </div>
    </div>
  )
}
