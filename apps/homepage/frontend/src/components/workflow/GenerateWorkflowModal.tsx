import { useState } from 'react'
import { X, Sparkles, Loader2, CheckCircle, AlertTriangle, RefreshCw, ChevronDown, Cpu, Zap, DollarSign } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useWorkflow, useGeneration, useLLMHealth } from '@/hooks/useWorkflowApi'
import type { ArtifactType, WorkflowScenario } from './types'

interface GenerateWorkflowModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess?: (artifacts: { id: string; type: ArtifactType; title: string }[]) => void
}

const SCENARIOS: { id: WorkflowScenario; label: string; description: string }[] = [
  { id: 'new_feature', label: 'New Feature', description: 'Full workflow: Discussion → ADR → SPEC → Plan' },
  { id: 'bug_fix', label: 'Bug Fix', description: 'Quick fix: Plan → Fragment' },
  { id: 'architecture_change', label: 'Architecture Change', description: 'Full workflow with ADR focus' },
  { id: 'enhancement', label: 'Enhancement', description: 'SPEC → Plan → Fragment' },
  { id: 'data_structure', label: 'Data Structure', description: 'Contract → Plan' },
]

export function GenerateWorkflowModal({ isOpen, onClose, onSuccess }: GenerateWorkflowModalProps) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [scenario, setScenario] = useState<WorkflowScenario>('new_feature')
  const [step, setStep] = useState<'input' | 'generating' | 'complete'>('input')
  const [generatedArtifacts, setGeneratedArtifacts] = useState<{ id: string; type: ArtifactType; title: string }[]>([])

  const [showModelSelector, setShowModelSelector] = useState(false)

  const { createWorkflow } = useWorkflow()
  const { generateFullWorkflow, loading: generating, error } = useGeneration()
  const { health: llmHealth, loading: healthLoading, refresh: refreshHealth, setModel } = useLLMHealth()

  const llmAvailable = llmHealth?.available ?? false
  const llmMessage = llmHealth?.message ?? 'Checking AI availability...'
  const llmModel = llmHealth?.model
  const models = llmHealth?.models ?? []

  const currentModelInfo = models.find(m => m.id === llmModel)

  const handleModelChange = async (modelId: string) => {
    await setModel(modelId)
    setShowModelSelector(false)
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'fast': return <Zap size={12} className="text-yellow-400" />
      case 'code': return <Cpu size={12} className="text-blue-400" />
      case 'premium': return <DollarSign size={12} className="text-purple-400" />
      default: return null
    }
  }

  const formatContext = (ctx: number) => {
    if (ctx >= 1_000_000) return `${(ctx / 1_000_000).toFixed(1)}M`
    if (ctx >= 1_000) return `${(ctx / 1_000).toFixed(0)}K`
    return ctx.toString()
  }

  const handleGenerate = async () => {
    if (!title.trim()) return

    setStep('generating')
    try {
      // Create workflow in AI-Full mode
      const workflow = await createWorkflow({
        mode: 'ai_full',
        scenario,
        title: title.trim(),
      })

      // Generate all artifacts
      const artifacts = await generateFullWorkflow(workflow.id)
      setGeneratedArtifacts(artifacts.map(a => ({ id: a.id, type: a.type, title: a.title })))
      setStep('complete')
    } catch (err) {
      console.error('Generation failed:', err)
      setStep('input')
    }
  }

  const handleComplete = () => {
    onSuccess?.(generatedArtifacts)
    handleClose()
  }

  const handleClose = () => {
    setTitle('')
    setDescription('')
    setScenario('new_feature')
    setStep('input')
    setGeneratedArtifacts([])
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60" onClick={handleClose} />
      <div className="relative w-full max-w-lg max-h-[90vh] flex flex-col bg-zinc-900 rounded-lg border border-zinc-700 shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-zinc-800">
          <div className="flex items-center gap-2">
            <Sparkles className="text-purple-400" size={20} />
            <h2 className="text-lg font-semibold">Generate Full Workflow</h2>
          </div>
          <button onClick={handleClose} className="p-1 hover:bg-zinc-800 rounded" title="Close">
            <X size={20} />
          </button>
        </div>

        {/* Content - scrollable when viewport is small */}
        <div className="p-4 overflow-y-auto flex-1 min-h-0">
          {step === 'input' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Title</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g., Add user authentication"
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Description (optional)</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Brief description of the feature..."
                  rows={3}
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded focus:outline-none focus:border-blue-500 resize-none"
                />
              </div>

              {/* Model Selector */}
              <div>
                <label className="block text-sm font-medium mb-1">AI Model</label>
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => setShowModelSelector(!showModelSelector)}
                    className="w-full flex items-center justify-between px-3 py-2 bg-zinc-800 border border-zinc-700 rounded hover:border-zinc-600 transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      {currentModelInfo && getCategoryIcon(currentModelInfo.category)}
                      <span>{currentModelInfo?.name || 'Select model...'}</span>
                    </div>
                    <ChevronDown size={16} className={cn('transition-transform', showModelSelector && 'rotate-180')} />
                  </button>

                  {showModelSelector && (
                    <div className="absolute z-10 mt-1 w-full bg-zinc-800 border border-zinc-700 rounded shadow-lg max-h-64 overflow-y-auto">
                      {models.map((model) => (
                        <button
                          key={model.id}
                          onClick={() => handleModelChange(model.id)}
                          className={cn(
                            'w-full text-left px-3 py-2 hover:bg-zinc-700 transition-colors',
                            model.id === llmModel && 'bg-purple-500/20 border-l-2 border-purple-500'
                          )}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              {getCategoryIcon(model.category)}
                              <span className="font-medium">{model.name}</span>
                              {model.reasoning && (
                                <span className="px-1.5 py-0.5 text-[10px] bg-green-500/20 text-green-400 rounded">
                                  reasoning
                                </span>
                              )}
                            </div>
                          </div>
                          <div className="flex items-center gap-3 mt-1 text-xs text-zinc-500">
                            <span>{formatContext(model.context_window)} ctx</span>
                            <span>{model.rpm} rpm</span>
                            <span>${model.input_price}/${model.output_price}</span>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                {currentModelInfo && (
                  <p className="mt-1 text-xs text-zinc-500">
                    {formatContext(currentModelInfo.context_window)} context • {currentModelInfo.rpm} req/min • ${currentModelInfo.input_price}/${ currentModelInfo.output_price} per M tokens
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Workflow Type</label>
                <div className="space-y-2">
                  {SCENARIOS.map((s) => (
                    <button
                      key={s.id}
                      onClick={() => setScenario(s.id)}
                      className={cn(
                        'w-full text-left p-3 rounded border transition-colors',
                        scenario === s.id
                          ? 'border-purple-500 bg-purple-500/10'
                          : 'border-zinc-700 hover:border-zinc-600'
                      )}
                    >
                      <div className="font-medium">{s.label}</div>
                      <div className="text-xs text-zinc-500">{s.description}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* LLM Status Banner */}
              {!llmAvailable && !healthLoading && (
                <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-amber-400">
                      <AlertTriangle size={16} />
                      <span className="text-sm font-medium">AI Generation Unavailable</span>
                    </div>
                    <button
                      onClick={() => refreshHealth()}
                      className="flex items-center gap-1 px-2 py-1 text-xs bg-amber-500/20 hover:bg-amber-500/30 rounded"
                    >
                      <RefreshCw size={12} />
                      Retry
                    </button>
                  </div>
                  <p className="mt-1 text-xs text-amber-400/80">{llmMessage}</p>
                </div>
              )}

              {llmAvailable && llmModel && (
                <div className="p-2 bg-green-500/10 border border-green-500/30 rounded flex items-center gap-2 text-green-400 text-sm">
                  <CheckCircle size={14} />
                  <span>Connected to {llmModel}</span>
                </div>
              )}

              {error && (
                <div className="p-3 bg-red-500/10 border border-red-500/30 rounded text-red-400 text-sm">
                  {error.message}
                </div>
              )}
            </div>
          )}

          {step === 'generating' && (
            <div className="flex flex-col items-center justify-center py-12">
              <Loader2 size={48} className="animate-spin text-purple-400 mb-4" />
              <p className="text-lg font-medium">Generating artifacts...</p>
              <p className="text-sm text-zinc-500">This may take a moment</p>
            </div>
          )}

          {step === 'complete' && (
            <div className="space-y-4">
              <div className="flex items-center justify-center py-4">
                <CheckCircle size={48} className="text-green-400" />
              </div>
              <p className="text-center text-lg font-medium">Workflow Generated!</p>
              <div className="space-y-2">
                <p className="text-sm text-zinc-500">Created artifacts:</p>
                {generatedArtifacts.map((artifact) => (
                  <div
                    key={artifact.id}
                    className="p-2 bg-zinc-800 rounded border border-zinc-700"
                  >
                    <span className="text-xs text-zinc-500 uppercase">{artifact.type}</span>
                    <p className="font-medium">{artifact.id}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-2 p-4 border-t border-zinc-800">
          <button
            onClick={handleClose}
            className="px-4 py-2 text-sm hover:bg-zinc-800 rounded"
          >
            Cancel
          </button>
          {step === 'input' && (
            <button
              onClick={handleGenerate}
              disabled={!title.trim() || generating || !llmAvailable}
              className="flex items-center gap-2 px-4 py-2 text-sm bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed rounded"
              title={!llmAvailable ? 'AI service unavailable' : undefined}
            >
              <Sparkles size={16} />
              Generate
            </button>
          )}
          {step === 'complete' && (
            <button
              onClick={handleComplete}
              className="px-4 py-2 text-sm bg-green-600 hover:bg-green-700 rounded"
            >
              Done
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
