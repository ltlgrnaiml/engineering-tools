/**
 * Workflow API hooks for DevTools.
 * Local implementation matching shared/frontend/src/hooks/useWorkflowApi.ts
 */

import { useState, useEffect, useCallback } from 'react'
import type { ArtifactSummary, ArtifactType, GraphResponse, WorkflowState, PromptResponse } from '../components/workflow/types'

const API_BASE = 'http://localhost:8000/api/devtools'

interface UseDataResult<T> {
  data: T | null
  loading: boolean
  error: Error | null
  refetch: () => void
}

export function useArtifacts(
  type?: ArtifactType,
  search?: string
): UseDataResult<ArtifactSummary[]> {
  const [data, setData] = useState<ArtifactSummary[] | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams()
      if (type) params.set('artifact_type', type)
      if (search) params.set('search', search)
      const query = params.toString()
      
      const res = await fetch(`${API_BASE}/artifacts${query ? `?${query}` : ''}`)
      if (!res.ok) throw new Error('Failed to fetch artifacts')
      const response = await res.json()
      setData(response.items)
    } catch (e) {
      setError(e instanceof Error ? e : new Error(String(e)))
    } finally {
      setLoading(false)
    }
  }, [type, search])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return { data, loading, error, refetch: fetchData }
}

export function useArtifactGraph(): UseDataResult<GraphResponse> {
  const [data, setData] = useState<GraphResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/artifacts/graph`)
      if (!res.ok) throw new Error('Failed to fetch graph')
      const response = await res.json()
      setData(response)
    } catch (e) {
      setError(e instanceof Error ? e : new Error(String(e)))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return { data, loading, error, refetch: fetchData }
}

interface CreateWorkflowRequest {
  mode: 'manual' | 'ai_lite' | 'ai_full'
  scenario: 'new_feature' | 'bug_fix' | 'architecture_change' | 'enhancement' | 'data_structure'
  title: string
}

interface UseWorkflowResult {
  workflow: WorkflowState | null
  loading: boolean
  error: Error | null
  createWorkflow: (request: CreateWorkflowRequest) => Promise<WorkflowState>
  advanceWorkflow: () => Promise<void>
  refetch: () => void
}

export function useWorkflow(workflowId?: string): UseWorkflowResult {
  const [workflow, setWorkflow] = useState<WorkflowState | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const fetchStatus = useCallback(async () => {
    if (!workflowId) return
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/workflows/${workflowId}/status`)
      if (!res.ok) throw new Error('Failed to fetch workflow status')
      const response = await res.json()
      setWorkflow(response.workflow)
    } catch (e) {
      setError(e instanceof Error ? e : new Error(String(e)))
    } finally {
      setLoading(false)
    }
  }, [workflowId])

  useEffect(() => {
    if (workflowId) fetchStatus()
  }, [workflowId, fetchStatus])

  const createWorkflow = useCallback(async (request: CreateWorkflowRequest) => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/workflows`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      })
      if (!res.ok) throw new Error('Failed to create workflow')
      const response = await res.json()
      setWorkflow(response.workflow)
      return response.workflow
    } catch (e) {
      const err = e instanceof Error ? e : new Error(String(e))
      setError(err)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const advanceWorkflow = useCallback(async () => {
    if (!workflowId) throw new Error('No workflow ID')
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/workflows/${workflowId}/advance`, { method: 'POST' })
      if (!res.ok) throw new Error('Failed to advance workflow')
      const response = await res.json()
      setWorkflow(response.workflow)
    } catch (e) {
      const err = e instanceof Error ? e : new Error(String(e))
      setError(err)
      throw err
    } finally {
      setLoading(false)
    }
  }, [workflowId])

  return { workflow, loading, error, createWorkflow, advanceWorkflow, refetch: fetchStatus }
}

interface UsePromptResult {
  prompt: PromptResponse | null
  loading: boolean
  error: Error | null
  fetchPrompt: (artifactId: string, targetType: ArtifactType) => Promise<PromptResponse>
  copyToClipboard: () => Promise<void>
}

export function usePrompt(): UsePromptResult {
  const [prompt, setPrompt] = useState<PromptResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const fetchPrompt = useCallback(async (artifactId: string, targetType: ArtifactType) => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams({ target_type: targetType })
      const res = await fetch(`${API_BASE}/artifacts/${artifactId}/prompt?${params}`)
      if (!res.ok) throw new Error('Failed to fetch prompt')
      const response = await res.json()
      setPrompt(response)
      return response
    } catch (e) {
      const err = e instanceof Error ? e : new Error(String(e))
      setError(err)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const copyToClipboard = useCallback(async () => {
    if (!prompt) throw new Error('No prompt to copy')
    await navigator.clipboard.writeText(prompt.prompt)
  }, [prompt])

  return { prompt, loading, error, fetchPrompt, copyToClipboard }
}

interface GenerationResult {
  loading: boolean
  error: Error | null
  generateArtifacts: (workflowId: string, targetTypes: ArtifactType[], context: Record<string, unknown>) => Promise<ArtifactSummary[]>
  generateFullWorkflow: (workflowId: string) => Promise<ArtifactSummary[]>
}

export function useGeneration(): GenerationResult {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const generateArtifacts = useCallback(async (
    workflowId: string,
    targetTypes: ArtifactType[],
    context: Record<string, unknown>
  ) => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/artifacts/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workflow_id: workflowId, target_types: targetTypes, context }),
      })
      if (!res.ok) throw new Error('Failed to generate artifacts')
      const response = await res.json()
      return response.artifacts
    } catch (e) {
      const err = e instanceof Error ? e : new Error(String(e))
      setError(err)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const generateFullWorkflow = useCallback(async (workflowId: string) => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/workflows/${workflowId}/generate-all`, { method: 'POST' })
      if (!res.ok) throw new Error('Failed to generate full workflow')
      const response = await res.json()
      return response.artifacts
    } catch (e) {
      const err = e instanceof Error ? e : new Error(String(e))
      setError(err)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  return { loading, error, generateArtifacts, generateFullWorkflow }
}

// =============================================================================
// LLM Health Check Hook
// =============================================================================

export interface ModelInfo {
  id: string
  name: string
  context_window: number
  rpm: number
  input_price: number
  output_price: number
  category: string
  reasoning: boolean
}

interface LLMHealthState {
  status: string
  message: string
  model: string | null
  available: boolean
  models: ModelInfo[]
}

interface UseLLMHealthResult {
  health: LLMHealthState | null
  loading: boolean
  error: Error | null
  refresh: () => Promise<void>
  setModel: (modelId: string) => Promise<boolean>
}

export function useLLMHealth(): UseLLMHealthResult {
  const [health, setHealth] = useState<LLMHealthState | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchHealth = useCallback(async (forceRefresh: boolean = false) => {
    setLoading(true)
    setError(null)
    try {
      const params = forceRefresh ? '?refresh=true' : ''
      const res = await fetch(`${API_BASE}/llm/health${params}`)
      if (!res.ok) throw new Error('Failed to check LLM health')
      const response = await res.json()
      setHealth(response)
    } catch (e) {
      setError(e instanceof Error ? e : new Error(String(e)))
      setHealth({
        status: 'error',
        message: 'Failed to check LLM status',
        model: null,
        available: false,
        models: [],
      })
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchHealth()
  }, [fetchHealth])

  const refresh = useCallback(async () => {
    await fetchHealth(true)
  }, [fetchHealth])

  const setModel = useCallback(async (modelId: string): Promise<boolean> => {
    try {
      const res = await fetch(`${API_BASE}/llm/model`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_id: modelId }),
      })
      if (!res.ok) return false
      const response = await res.json()
      if (response.success && health) {
        setHealth({ ...health, model: modelId })
      }
      return response.success
    } catch {
      return false
    }
  }, [health])

  return { health, loading, error, refresh, setModel }
}
