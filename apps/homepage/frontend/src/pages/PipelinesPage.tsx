import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { GitBranch, Play, Clock, CheckCircle, XCircle, Loader2 } from 'lucide-react'
import { formatDate } from '@/lib/utils'
import { cn } from '@/lib/utils'

interface Pipeline {
  id: string
  name: string
  description: string
  state: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  steps: { type: string; state: string }[]
  created_at: string
}

const stateIcons = {
  pending: Clock,
  running: Loader2,
  completed: CheckCircle,
  failed: XCircle,
  cancelled: XCircle,
}

const stateColors = {
  pending: 'text-slate-500',
  running: 'text-blue-500',
  completed: 'text-green-500',
  failed: 'text-red-500',
  cancelled: 'text-slate-400',
}

async function fetchPipelines(): Promise<Pipeline[]> {
  const response = await fetch('/api/v1/pipelines')
  if (!response.ok) throw new Error('Failed to fetch pipelines')
  return response.json()
}

export function PipelinesPage() {
  const { data: pipelines, isLoading, error } = useQuery({
    queryKey: ['pipelines'],
    queryFn: fetchPipelines,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        Failed to load pipelines. Make sure the gateway is running.
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">Pipelines</h1>
        <Link
          to="/pipelines/new"
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg text-sm font-medium transition-colors"
        >
          <Play className="w-4 h-4" />
          New Pipeline
        </Link>
      </div>

      {pipelines?.length === 0 ? (
        <div className="bg-slate-50 border border-slate-200 rounded-lg p-8 text-center">
          <GitBranch className="w-12 h-12 text-slate-400 mx-auto" />
          <h3 className="mt-4 text-lg font-medium text-slate-900">No Pipelines Yet</h3>
          <p className="mt-2 text-sm text-slate-600">
            Create a pipeline to chain multiple tools together.
          </p>
        </div>
      ) : (
        <div className="grid gap-4">
          {pipelines?.map((pipeline) => {
            const StateIcon = stateIcons[pipeline.state]
            return (
              <div
                key={pipeline.id}
                className="bg-white border border-slate-200 rounded-lg p-4 hover:border-slate-300 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-medium text-slate-900">{pipeline.name}</h3>
                    <p className="text-sm text-slate-600 mt-1">{pipeline.description}</p>
                  </div>
                  <div className={cn('flex items-center gap-1', stateColors[pipeline.state])}>
                    <StateIcon className={cn('w-4 h-4', pipeline.state === 'running' && 'animate-spin')} />
                    <span className="text-sm capitalize">{pipeline.state}</span>
                  </div>
                </div>
                <div className="mt-4 flex items-center gap-2 text-xs text-slate-500">
                  <span>{pipeline.steps.length} steps</span>
                  <span>•</span>
                  <span>{formatDate(pipeline.created_at)}</span>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
