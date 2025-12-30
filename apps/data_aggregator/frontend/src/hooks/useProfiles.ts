/**
 * React hooks for profile-driven extraction API.
 * 
 * Per DESIGN §4, §9: Provides hooks for:
 * - Listing available profiles
 * - Fetching profile tables (grouped by level)
 * - Executing profile extraction
 * - Applying context to extracted tables
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useDebugFetch } from '../components/debug'
import type {
  ProfileSummary,
  ProfileTablesResponse,
  ExtractionResponse,
  ApplyContextRequest,
  ApplyContextResponse,
} from '../types/profile'

/**
 * Hook to fetch available profiles.
 */
export function useProfiles() {
  const debugFetch = useDebugFetch()

  return useQuery({
    queryKey: ['dat-profiles'],
    queryFn: async (): Promise<ProfileSummary[]> => {
      const response = await debugFetch('/api/dat/profiles')
      if (!response.ok) throw new Error('Failed to fetch profiles')
      return response.json()
    },
  })
}

/**
 * Hook to fetch tables defined in a profile.
 * Tables are grouped by level (run, image, etc.)
 */
export function useProfileTables(profileId: string | null) {
  const debugFetch = useDebugFetch()

  return useQuery({
    queryKey: ['dat-profile-tables', profileId],
    queryFn: async (): Promise<ProfileTablesResponse> => {
      if (!profileId) throw new Error('No profile ID')
      const response = await debugFetch(`/api/dat/profiles/${profileId}/tables`)
      if (!response.ok) throw new Error('Failed to fetch profile tables')
      return response.json()
    },
    enabled: !!profileId,
  })
}

/**
 * Profile context configuration response type.
 */
export interface ProfileContextResponse {
  profile_id: string
  profile_name: string
  context_defaults: {
    defaults: Record<string, string>
    regex_patterns: Array<{
      field: string
      pattern: string
      scope: string
      required: boolean
      description: string
      example: string
    }>
    content_patterns: Array<{
      field: string
      path: string
      required: boolean
      default: string | null
      description: string
    }>
    allow_user_override: string[]
  } | null
  contexts: Array<{
    name: string
    level: string
    paths: string[]
    key_map: Record<string, string>
    primary_keys: string[]
  }>
}

/**
 * Hook to fetch context configuration from a profile.
 * Returns regex patterns, defaults, content patterns for UI display.
 */
export function useProfileContext(profileId: string | null) {
  const debugFetch = useDebugFetch()

  return useQuery({
    queryKey: ['dat-profile-context', profileId],
    queryFn: async (): Promise<ProfileContextResponse> => {
      if (!profileId) throw new Error('No profile ID')
      const response = await debugFetch(`/api/dat/profiles/${profileId}/context`)
      if (!response.ok) throw new Error('Failed to fetch profile context')
      return response.json()
    },
    enabled: !!profileId,
  })
}

/**
 * Hook to execute profile-driven extraction.
 * Returns tables and context SEPARATELY per DESIGN §4, §9.
 */
export function useProfileExtraction(runId: string) {
  const debugFetch = useDebugFetch()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (selectedTables?: string[]): Promise<ExtractionResponse> => {
      const response = await debugFetch(
        `/api/dat/runs/${runId}/stages/parse/profile-extract`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            selected_tables: selectedTables,
          }),
        }
      )
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Extraction failed' }))
        throw new Error(error.detail || 'Profile extraction failed')
      }
      return response.json()
    },
    onSuccess: (data) => {
      // Cache the extraction result for use by apply-context
      queryClient.setQueryData(['dat-extraction', runId], data)
    },
  })
}

/**
 * Hook to get cached extraction result.
 */
export function useExtractionResult(runId: string) {
  const queryClient = useQueryClient()
  return queryClient.getQueryData<ExtractionResponse>(['dat-extraction', runId])
}

/**
 * Hook to apply context to extracted tables.
 * Called after extraction with user's context toggle selections.
 */
export function useApplyContext(runId: string) {
  const debugFetch = useDebugFetch()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (request: ApplyContextRequest): Promise<ApplyContextResponse> => {
      const response = await debugFetch(
        `/api/dat/runs/${runId}/stages/parse/apply-context`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(request),
        }
      )
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Apply context failed' }))
        throw new Error(error.detail || 'Failed to apply context')
      }
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dat-run', runId] })
    },
  })
}

/**
 * Combined hook for the full extraction flow.
 * Provides state management for the extraction process.
 */
export function useExtractionFlow(runId: string) {
  const extraction = useProfileExtraction(runId)
  const applyContext = useApplyContext(runId)
  const cachedResult = useExtractionResult(runId)

  return {
    // Extraction state
    extraction,
    extractionResult: extraction.data || cachedResult,
    isExtracting: extraction.isPending,
    extractionError: extraction.error,

    // Apply context state
    applyContext,
    isApplyingContext: applyContext.isPending,
    applyContextError: applyContext.error,
    appliedResult: applyContext.data,

    // Combined loading state
    isLoading: extraction.isPending || applyContext.isPending,
  }
}
