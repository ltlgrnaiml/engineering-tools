import { useCallback } from 'react'
import { useDebugOptional } from './DebugContext'

/**
 * A fetch wrapper that automatically logs all API calls to the debug panel.
 * Falls back to regular fetch if debug context is not available.
 */
export function useDebugFetch() {
  const debug = useDebugOptional()
  
  const debugFetch = useCallback(async (
    url: string,
    options?: RequestInit
  ): Promise<Response> => {
    const method = options?.method || 'GET'
    let requestBody: unknown = undefined
    
    if (options?.body) {
      try {
        requestBody = JSON.parse(options.body as string)
      } catch {
        requestBody = options.body
      }
    }
    
    const startTime = Date.now()
    let callId = ''
    
    if (debug) {
      callId = debug.logAPI({
        method,
        url,
        requestBody,
        pending: true,
      })
    }
    
    try {
      const response = await fetch(url, options)
      const duration = Date.now() - startTime
      
      let responseBody: unknown = undefined
      const clonedResponse = response.clone()
      try {
        responseBody = await clonedResponse.json()
      } catch {
        try {
          responseBody = await clonedResponse.text()
        } catch {
          responseBody = '<unable to read body>'
        }
      }
      
      if (debug && callId) {
        debug.updateAPI(callId, {
          responseStatus: response.status,
          responseBody,
          duration,
          pending: false,
          error: response.ok ? undefined : `HTTP ${response.status}`,
        })
      }
      
      return response
    } catch (error) {
      const duration = Date.now() - startTime
      
      if (debug && callId) {
        debug.updateAPI(callId, {
          duration,
          pending: false,
          error: error instanceof Error ? error.message : String(error),
        })
      }
      
      throw error
    }
  }, [debug])
  
  return debugFetch
}

/**
 * Creates a standalone debug fetch function that can be used outside of React components.
 * This is useful for integrating with existing code that doesn't use hooks.
 */
export function createDebugFetch(
  logAPI: (entry: { method: string; url: string; requestBody?: unknown; pending: boolean }) => string,
  updateAPI: (id: string, updates: { responseStatus?: number; responseBody?: unknown; duration?: number; pending: boolean; error?: string }) => void
) {
  return async (url: string, options?: RequestInit): Promise<Response> => {
    const method = options?.method || 'GET'
    let requestBody: unknown = undefined
    
    if (options?.body) {
      try {
        requestBody = JSON.parse(options.body as string)
      } catch {
        requestBody = options.body
      }
    }
    
    const startTime = Date.now()
    const callId = logAPI({
      method,
      url,
      requestBody,
      pending: true,
    })
    
    try {
      const response = await fetch(url, options)
      const duration = Date.now() - startTime
      
      let responseBody: unknown = undefined
      const clonedResponse = response.clone()
      try {
        responseBody = await clonedResponse.json()
      } catch {
        try {
          responseBody = await clonedResponse.text()
        } catch {
          responseBody = '<unable to read body>'
        }
      }
      
      updateAPI(callId, {
        responseStatus: response.status,
        responseBody,
        duration,
        pending: false,
        error: response.ok ? undefined : `HTTP ${response.status}`,
      })
      
      return response
    } catch (error) {
      const duration = Date.now() - startTime
      
      updateAPI(callId, {
        duration,
        pending: false,
        error: error instanceof Error ? error.message : String(error),
      })
      
      throw error
    }
  }
}
