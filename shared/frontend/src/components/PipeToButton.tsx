import { useState } from 'react'
import { ArrowRight, Presentation, BarChart3, Loader2 } from 'lucide-react'

type TargetTool = 'pptx' | 'sov'

interface PipeToButtonProps {
  datasetId: string
  targetTool: TargetTool
  disabled?: boolean
  onSuccess?: (pipelineId: string) => void
  onError?: (error: Error) => void
  className?: string
}

const toolConfig = {
  pptx: {
    label: 'PowerPoint',
    icon: Presentation,
    color: 'bg-orange-500 hover:bg-orange-600',
  },
  sov: {
    label: 'SOV Analyzer',
    icon: BarChart3,
    color: 'bg-purple-500 hover:bg-purple-600',
  },
}

export function PipeToButton({
  datasetId,
  targetTool,
  disabled = false,
  onSuccess,
  onError,
  className = '',
}: PipeToButtonProps) {
  const [isPiping, setIsPiping] = useState(false)

  const config = toolConfig[targetTool]
  const Icon = config.icon

  async function handlePipe() {
    if (!datasetId || isPiping) return

    setIsPiping(true)
    try {
      const response = await fetch('/api/pipelines', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: `Pipe to ${config.label}`,
          description: `Pipeline from DataSet ${datasetId} to ${config.label}`,
          steps: [
            {
              type: targetTool,
              config: { input_dataset_id: datasetId },
            },
          ],
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to create pipeline')
      }

      const pipeline = await response.json()
      onSuccess?.(pipeline.id)

      // Navigate to the target tool
      window.location.href = `/tools/${targetTool}?dataset=${datasetId}`
    } catch (error) {
      onError?.(error instanceof Error ? error : new Error('Unknown error'))
    } finally {
      setIsPiping(false)
    }
  }

  return (
    <button
      type="button"
      onClick={handlePipe}
      disabled={disabled || isPiping || !datasetId}
      className={`
        inline-flex items-center gap-2 px-4 py-2 rounded-lg
        text-white font-medium text-sm
        transition-colors
        disabled:opacity-50 disabled:cursor-not-allowed
        ${config.color}
        ${className}
      `}
    >
      {isPiping ? (
        <Loader2 className="w-4 h-4 animate-spin" />
      ) : (
        <>
          <ArrowRight className="w-4 h-4" />
          <Icon className="w-4 h-4" />
        </>
      )}
      <span>Pipe to {config.label}</span>
    </button>
  )
}
