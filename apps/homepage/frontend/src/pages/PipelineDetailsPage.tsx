import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  ArrowLeft, 
  GitBranch, 
  Calendar, 
  Play,
  Square,
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
  FileSpreadsheet,
  Presentation,
  BarChart3,
  AlertCircle
} from 'lucide-react'
import { formatDate, cn } from '@/lib/utils'

type StepType = 'dat' | 'sov' | 'pptx'
type StepState = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
type PipelineState = 'draft' | 'ready' | 'running' | 'completed' | 'failed' | 'cancelled'

interface PipelineStep {
  step_id: string
  step_type: StepType
  config: Record<string, unknown>
  state: StepState
  input_dataset_id?: string
  output_dataset_id?: string
  error_message?: string
  started_at?: string
  completed_at?: string
}

interface Pipeline {
  pipeline_id: string
  name: string
  description?: string
  steps: PipelineStep[]
  state: PipelineState
  created_at: string
  started_at?: string
  completed_at?: string
}

async function fetchPipeline(id: string): Promise<Pipeline> {
  const response = await fetch(`/api/v1/pipelines/${id}`)
  if (!response.ok) throw new Error('Failed to fetch pipeline')
  return response.json()
}

async function executePipeline(id: string): Promise<Pipeline> {
  const response = await fetch(`/api/v1/pipelines/${id}/execute`, { method: 'POST' })
  if (!response.ok) throw new Error('Failed to execute pipeline')
  return response.json()
}

async function cancelPipeline(id: string): Promise<Pipeline> {
  const response = await fetch(`/api/v1/pipelines/${id}/cancel`, { method: 'POST' })
  if (!response.ok) throw new Error('Failed to cancel pipeline')
  return response.json()
}

const stepTypeConfig: Record<StepType, { icon: typeof FileSpreadsheet; label: string; color: string }> = {
  dat: { icon: FileSpreadsheet, label: 'Data Aggregator', color: 'bg-emerald-500' },
  sov: { icon: BarChart3, label: 'SOV Analyzer', color: 'bg-purple-500' },
  pptx: { icon: Presentation, label: 'PowerPoint Generator', color: 'bg-orange-500' },
}

const stepStateConfig: Record<StepState, { icon: typeof Clock; label: string; color: string }> = {
  pending: { icon: Clock, label: 'Pending', color: 'text-slate-500' },
  running: { icon: Loader2, label: 'Running', color: 'text-blue-500' },
  completed: { icon: CheckCircle2, label: 'Completed', color: 'text-green-500' },
  failed: { icon: XCircle, label: 'Failed', color: 'text-red-500' },
  cancelled: { icon: Square, label: 'Cancelled', color: 'text-amber-500' },
}

const pipelineStateConfig: Record<PipelineState, { label: string; color: string }> = {
  draft: { label: 'Draft', color: 'bg-slate-100 text-slate-800' },
  ready: { label: 'Ready', color: 'bg-blue-100 text-blue-800' },
  running: { label: 'Running', color: 'bg-blue-100 text-blue-800' },
  completed: { label: 'Completed', color: 'bg-green-100 text-green-800' },
  failed: { label: 'Failed', color: 'bg-red-100 text-red-800' },
  cancelled: { label: 'Cancelled', color: 'bg-amber-100 text-amber-800' },
}

export function PipelineDetailsPage() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()

  const { data: pipeline, isLoading, error } = useQuery({
    queryKey: ['pipeline', id],
    queryFn: () => fetchPipeline(id!),
    enabled: !!id,
    refetchInterval: (query) => {
      // Poll while running
      if (query.state.data?.state === 'running') return 2000
      return false
    },
  })

  const executeMutation = useMutation({
    mutationFn: () => executePipeline(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pipeline', id] })
    },
  })

  const cancelMutation = useMutation({
    mutationFn: () => cancelPipeline(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pipeline', id] })
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    )
  }

  if (error || !pipeline) {
    return (
      <div className="text-center py-16">
        <GitBranch className="w-12 h-12 mx-auto mb-4 text-slate-300" />
        <h2 className="text-xl font-semibold text-slate-900">Pipeline Not Found</h2>
        <p className="mt-2 text-slate-600">The requested pipeline could not be found.</p>
        <Link to="/pipelines" className="mt-4 inline-block text-primary-600 hover:text-primary-700">
          ← Back to Pipelines
        </Link>
      </div>
    )
  }

  const canExecute = pipeline.state === 'ready' || pipeline.state === 'draft'
  const canCancel = pipeline.state === 'running'
  const stateConfig = pipelineStateConfig[pipeline.state]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <Link 
            to="/pipelines" 
            className="inline-flex items-center gap-1 text-sm text-slate-600 hover:text-slate-900 mb-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Pipelines
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-slate-900">{pipeline.name}</h1>
            <span className={`px-2 py-1 rounded text-sm font-medium ${stateConfig.color}`}>
              {stateConfig.label}
            </span>
          </div>
          {pipeline.description && (
            <p className="mt-1 text-slate-600">{pipeline.description}</p>
          )}
        </div>
        <div className="flex gap-2">
          {canExecute && (
            <button
              onClick={() => executeMutation.mutate()}
              disabled={executeMutation.isPending}
              className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
            >
              {executeMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Play className="w-4 h-4" />
              )}
              Execute Pipeline
            </button>
          )}
          {canCancel && (
            <button
              onClick={() => cancelMutation.mutate()}
              disabled={cancelMutation.isPending}
              className="inline-flex items-center gap-2 px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
            >
              {cancelMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Square className="w-4 h-4" />
              )}
              Cancel
            </button>
          )}
        </div>
      </div>

      {/* Metadata */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <div className="flex items-center gap-2 text-slate-600 text-sm mb-1">
            <GitBranch className="w-4 h-4" />
            Steps
          </div>
          <div className="text-2xl font-semibold text-slate-900">
            {pipeline.steps.length}
          </div>
        </div>
        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <div className="flex items-center gap-2 text-slate-600 text-sm mb-1">
            <Calendar className="w-4 h-4" />
            Created
          </div>
          <div className="text-lg font-semibold text-slate-900">
            {formatDate(pipeline.created_at)}
          </div>
        </div>
        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <div className="flex items-center gap-2 text-slate-600 text-sm mb-1">
            <Clock className="w-4 h-4" />
            Duration
          </div>
          <div className="text-lg font-semibold text-slate-900">
            {pipeline.started_at && pipeline.completed_at
              ? `${Math.round((new Date(pipeline.completed_at).getTime() - new Date(pipeline.started_at).getTime()) / 1000)}s`
              : pipeline.state === 'running'
              ? 'In progress...'
              : '-'
            }
          </div>
        </div>
      </div>

      {/* Steps */}
      <div className="bg-white rounded-lg border border-slate-200 p-4">
        <h2 className="font-semibold text-slate-900 mb-4">Pipeline Steps</h2>
        <div className="space-y-4">
          {pipeline.steps.map((step, index) => {
            const typeConfig = stepTypeConfig[step.step_type]
            const stateConf = stepStateConfig[step.state]
            const StateIcon = stateConf.icon
            const TypeIcon = typeConfig.icon

            return (
              <div 
                key={step.step_id}
                className={cn(
                  'border rounded-lg p-4 transition-colors',
                  step.state === 'running' && 'border-blue-300 bg-blue-50',
                  step.state === 'completed' && 'border-green-200 bg-green-50',
                  step.state === 'failed' && 'border-red-200 bg-red-50',
                  step.state === 'pending' && 'border-slate-200',
                )}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex items-center justify-center w-8 h-8 rounded-full bg-slate-100 text-slate-600 text-sm font-medium">
                      {index + 1}
                    </div>
                    <div className={cn('w-10 h-10 rounded-lg flex items-center justify-center', typeConfig.color)}>
                      <TypeIcon className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <div className="font-medium text-slate-900">{typeConfig.label}</div>
                      <div className="text-sm text-slate-500">Step ID: {step.step_id}</div>
                    </div>
                  </div>
                  <div className={cn('flex items-center gap-2', stateConf.color)}>
                    <StateIcon className={cn('w-5 h-5', step.state === 'running' && 'animate-spin')} />
                    <span className="font-medium">{stateConf.label}</span>
                  </div>
                </div>

                {/* Step Details */}
                <div className="mt-4 pl-11 space-y-2">
                  {step.input_dataset_id && (
                    <div className="text-sm">
                      <span className="text-slate-500">Input: </span>
                      <Link 
                        to={`/datasets/${step.input_dataset_id}`}
                        className="text-primary-600 hover:underline"
                      >
                        {step.input_dataset_id}
                      </Link>
                    </div>
                  )}
                  {step.output_dataset_id && (
                    <div className="text-sm">
                      <span className="text-slate-500">Output: </span>
                      <Link 
                        to={`/datasets/${step.output_dataset_id}`}
                        className="text-primary-600 hover:underline"
                      >
                        {step.output_dataset_id}
                      </Link>
                    </div>
                  )}
                  {step.error_message && (
                    <div className="flex items-start gap-2 p-2 bg-red-100 rounded text-sm text-red-800">
                      <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                      {step.error_message}
                    </div>
                  )}
                  {Object.keys(step.config).length > 0 && (
                    <details className="text-sm">
                      <summary className="text-slate-500 cursor-pointer hover:text-slate-700">
                        Configuration
                      </summary>
                      <pre className="mt-2 p-2 bg-slate-100 rounded text-xs overflow-x-auto">
                        {JSON.stringify(step.config, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
