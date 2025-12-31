/**
 * React hooks for DevTools Workflow API.
 * Provides data fetching with loading/error states.
 */

import { useState, useEffect, useCallback } from 'react';
import type {
  ArtifactSummary,
  ArtifactType,
  GraphResponse,
  WorkflowState,
  CreateWorkflowRequest,
  PromptResponse,
} from '../types/workflow';
import {
  listArtifacts,
  getGraph,
  createWorkflow as createWorkflowApi,
  getWorkflowStatus,
  advanceWorkflow as advanceWorkflowApi,
  getPrompt,
} from '../api/workflowClient';

interface UseDataResult<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  refetch: () => void;
}

export function useArtifacts(
  type?: ArtifactType,
  search?: string
): UseDataResult<ArtifactSummary[]> {
  const [data, setData] = useState<ArtifactSummary[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await listArtifacts(type, search);
      setData(response.items);
    } catch (e) {
      setError(e instanceof Error ? e : new Error(String(e)));
    } finally {
      setLoading(false);
    }
  }, [type, search]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

export function useArtifactGraph(): UseDataResult<GraphResponse> {
  const [data, setData] = useState<GraphResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getGraph();
      setData(response);
    } catch (e) {
      setError(e instanceof Error ? e : new Error(String(e)));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

interface UseWorkflowResult {
  workflow: WorkflowState | null;
  loading: boolean;
  error: Error | null;
  createWorkflow: (request: CreateWorkflowRequest) => Promise<WorkflowState>;
  advanceWorkflow: () => Promise<void>;
  refetch: () => void;
}

export function useWorkflow(workflowId?: string): UseWorkflowResult {
  const [workflow, setWorkflow] = useState<WorkflowState | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchStatus = useCallback(async () => {
    if (!workflowId) return;
    setLoading(true);
    setError(null);
    try {
      const response = await getWorkflowStatus(workflowId);
      setWorkflow(response.workflow);
    } catch (e) {
      setError(e instanceof Error ? e : new Error(String(e)));
    } finally {
      setLoading(false);
    }
  }, [workflowId]);

  useEffect(() => {
    if (workflowId) {
      fetchStatus();
    }
  }, [workflowId, fetchStatus]);

  const createWorkflow = useCallback(async (request: CreateWorkflowRequest) => {
    setLoading(true);
    setError(null);
    try {
      const response = await createWorkflowApi(request);
      setWorkflow(response.workflow);
      return response.workflow;
    } catch (e) {
      const err = e instanceof Error ? e : new Error(String(e));
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const advanceWorkflow = useCallback(async () => {
    if (!workflowId) throw new Error('No workflow ID');
    setLoading(true);
    setError(null);
    try {
      const response = await advanceWorkflowApi(workflowId);
      setWorkflow(response.workflow);
    } catch (e) {
      const err = e instanceof Error ? e : new Error(String(e));
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [workflowId]);

  return {
    workflow,
    loading,
    error,
    createWorkflow,
    advanceWorkflow,
    refetch: fetchStatus,
  };
}

interface UsePromptResult {
  prompt: PromptResponse | null;
  loading: boolean;
  error: Error | null;
  fetchPrompt: (artifactId: string, targetType: ArtifactType) => Promise<PromptResponse>;
  copyToClipboard: () => Promise<void>;
}

export function usePrompt(): UsePromptResult {
  const [prompt, setPrompt] = useState<PromptResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchPrompt = useCallback(async (artifactId: string, targetType: ArtifactType) => {
    setLoading(true);
    setError(null);
    try {
      const response = await getPrompt(artifactId, targetType);
      setPrompt(response);
      return response;
    } catch (e) {
      const err = e instanceof Error ? e : new Error(String(e));
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const copyToClipboard = useCallback(async () => {
    if (!prompt) throw new Error('No prompt to copy');
    await navigator.clipboard.writeText(prompt.prompt);
  }, [prompt]);

  return { prompt, loading, error, fetchPrompt, copyToClipboard };
}

export default {
  useArtifacts,
  useArtifactGraph,
  useWorkflow,
  usePrompt,
};
