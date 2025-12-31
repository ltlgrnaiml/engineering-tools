/**
 * Workflow API Client for DevTools.
 * Provides typed methods for all workflow endpoints.
 */

import type {
  ArtifactListResponse,
  ArtifactType,
  CreateWorkflowRequest,
  GenerationRequest,
  GenerationResponse,
  GraphResponse,
  PromptResponse,
  WorkflowResponse,
} from '../types/workflow';

// API base URL - can be overridden via environment or config
const API_BASE = (typeof window !== 'undefined' && (window as any).__API_URL__) 
  || 'http://localhost:8000/api/devtools';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`API Error ${response.status}: ${error}`);
  }

  return response.json();
}

export async function listArtifacts(
  type?: ArtifactType,
  search?: string
): Promise<ArtifactListResponse> {
  const params = new URLSearchParams();
  if (type) params.set('type', type);
  if (search) params.set('search', search);

  const query = params.toString();
  const url = `${API_BASE}/artifacts${query ? `?${query}` : ''}`;

  return fetchJson<ArtifactListResponse>(url);
}

export async function getGraph(): Promise<GraphResponse> {
  return fetchJson<GraphResponse>(`${API_BASE}/artifacts/graph`);
}

export async function createWorkflow(
  request: CreateWorkflowRequest
): Promise<WorkflowResponse> {
  return fetchJson<WorkflowResponse>(`${API_BASE}/workflows`, {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export async function getWorkflowStatus(
  workflowId: string
): Promise<WorkflowResponse> {
  return fetchJson<WorkflowResponse>(`${API_BASE}/workflows/${workflowId}/status`);
}

export async function advanceWorkflow(
  workflowId: string
): Promise<WorkflowResponse> {
  return fetchJson<WorkflowResponse>(`${API_BASE}/workflows/${workflowId}/advance`, {
    method: 'POST',
  });
}

export async function getPrompt(
  artifactId: string,
  targetType: ArtifactType
): Promise<PromptResponse> {
  const params = new URLSearchParams({ target_type: targetType });
  return fetchJson<PromptResponse>(`${API_BASE}/artifacts/${artifactId}/prompt?${params}`);
}

export async function generateArtifacts(
  request: GenerationRequest
): Promise<GenerationResponse> {
  return fetchJson<GenerationResponse>(`${API_BASE}/artifacts/generate`, {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export async function generateFullWorkflow(
  workflowId: string
): Promise<GenerationResponse> {
  return fetchJson<GenerationResponse>(`${API_BASE}/workflows/${workflowId}/generate-all`, {
    method: 'POST',
  });
}

export const workflowClient = {
  listArtifacts,
  getGraph,
  createWorkflow,
  getWorkflowStatus,
  advanceWorkflow,
  getPrompt,
  generateArtifacts,
  generateFullWorkflow,
};

export default workflowClient;
