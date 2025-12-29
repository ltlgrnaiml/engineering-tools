import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useDebugFetch } from '../components/debug'

export interface DATRun {
  run_id: string
  current_stage: string
  stages: Record<string, {
    state: 'unlocked' | 'locked'
    locked_at?: string
    data?: unknown
  }>
  created_at: string
}

async function fetchRun(runId: string, debugFetch: any): Promise<DATRun> {
  const response = await debugFetch(`/api/dat/runs/${runId}`)
  if (!response.ok) throw new Error('Failed to fetch run')
  return response.json()
}

async function createNewRun(debugFetch: any): Promise<DATRun> {
  console.log('Creating new run...')
  const response = await debugFetch('/api/dat/runs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  })
  console.log('Response status:', response.status, response.statusText)
  if (!response.ok) {
    const errorText = await response.text()
    console.error(`Create run failed: ${response.status} ${response.statusText}`, errorText)
    throw new Error(`Failed to create run: ${response.status} - ${errorText}`)
  }
  const data = await response.json()
  console.log('Run created:', data)
  return data
}

export function useRun(runId: string | null) {
  const queryClient = useQueryClient()
  const debugFetch = useDebugFetch()

  const { data: run, isLoading, error } = useQuery({
    queryKey: ['dat-run', runId],
    queryFn: () => fetchRun(runId!, debugFetch),
    enabled: !!runId,
  })

  const createMutation = useMutation({
    mutationFn: () => createNewRun(debugFetch),
    onSuccess: (newRun) => {
      queryClient.setQueryData(['dat-run', newRun.run_id], newRun)
    },
  })

  return {
    run,
    isLoading,
    error,
    createRun: createMutation.mutateAsync,
  }
}

export function useStageAction(runId: string) {
  const queryClient = useQueryClient()
  const debugFetch = useDebugFetch()

  const lockStage = useMutation({
    mutationFn: async ({ stage, data }: { stage: string; data: unknown }) => {
      const response = await debugFetch(`/api/dat/runs/${runId}/stages/${stage}/lock`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
      if (!response.ok) throw new Error('Failed to lock stage')
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dat-run', runId] })
    },
  })

  const unlockStage = useMutation({
    mutationFn: async (stage: string) => {
      const response = await debugFetch(`/api/dat/runs/${runId}/stages/${stage}/unlock`, {
        method: 'POST',
      })
      if (!response.ok) throw new Error('Failed to unlock stage')
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dat-run', runId] })
    },
  })

  return { lockStage, unlockStage }
}
