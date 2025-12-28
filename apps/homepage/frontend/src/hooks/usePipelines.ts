import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

export interface PipelineRef {
  pipeline_id: string
  name: string
  state: 'draft' | 'queued' | 'running' | 'completed' | 'failed' | 'cancelled'
  step_count: number
  current_step: number
  created_at: string
  updated_at: string | null
}

export interface PipelineStep {
  step_index: number
  step_type: string
  name?: string
  input_dataset_ids: string[]
  output_dataset_id?: string
  config: Record<string, unknown>
  state: 'pending' | 'running' | 'completed' | 'skipped' | 'failed' | 'cancelled'
}

export interface Pipeline extends PipelineRef {
  description?: string
  steps: PipelineStep[]
  tags: string[]
}

export interface CreatePipelineRequest {
  name: string
  description?: string
  steps: Omit<PipelineStep, 'state' | 'output_dataset_id'>[]
  tags?: string[]
  auto_execute?: boolean
}

async function fetchPipelines(): Promise<PipelineRef[]> {
  const response = await fetch('/api/v1/pipelines')
  if (!response.ok) throw new Error('Failed to fetch pipelines')
  return response.json()
}

async function fetchPipeline(pipelineId: string): Promise<Pipeline> {
  const response = await fetch(`/api/v1/pipelines/${pipelineId}`)
  if (!response.ok) throw new Error('Failed to fetch pipeline')
  return response.json()
}

async function createPipeline(request: CreatePipelineRequest): Promise<Pipeline> {
  const response = await fetch('/api/v1/pipelines', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })
  if (!response.ok) throw new Error('Failed to create pipeline')
  return response.json()
}

async function executePipeline(pipelineId: string): Promise<Pipeline> {
  const response = await fetch(`/api/v1/pipelines/${pipelineId}/execute`, {
    method: 'POST',
  })
  if (!response.ok) throw new Error('Failed to execute pipeline')
  return response.json()
}

async function cancelPipeline(pipelineId: string): Promise<Pipeline> {
  const response = await fetch(`/api/v1/pipelines/${pipelineId}/cancel`, {
    method: 'POST',
  })
  if (!response.ok) throw new Error('Failed to cancel pipeline')
  return response.json()
}

export function usePipelines() {
  return useQuery<PipelineRef[]>({
    queryKey: ['pipelines'],
    queryFn: fetchPipelines,
  })
}

export function usePipeline(pipelineId: string) {
  return useQuery<Pipeline>({
    queryKey: ['pipeline', pipelineId],
    queryFn: () => fetchPipeline(pipelineId),
    enabled: !!pipelineId,
  })
}

export function useCreatePipeline() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createPipeline,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pipelines'] })
    },
  })
}

export function useExecutePipeline() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: executePipeline,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['pipelines'] })
      queryClient.invalidateQueries({ queryKey: ['pipeline', data.pipeline_id] })
    },
  })
}

export function useCancelPipeline() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: cancelPipeline,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['pipelines'] })
      queryClient.invalidateQueries({ queryKey: ['pipeline', data.pipeline_id] })
    },
  })
}
