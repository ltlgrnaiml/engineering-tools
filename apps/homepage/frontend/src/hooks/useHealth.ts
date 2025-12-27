import { useQuery } from '@tanstack/react-query'

export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy'
  version: string
  tools: {
    dat: 'available' | 'coming_soon' | 'maintenance' | 'error'
    sov: 'available' | 'coming_soon' | 'maintenance' | 'error'
    pptx: 'available' | 'coming_soon' | 'maintenance' | 'error'
  }
  storage?: {
    datasets: number
    pipelines: number
    total_size_mb: number
  }
}

async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch('/api/health')
  if (!response.ok) throw new Error('Health check failed')
  return response.json()
}

export function useHealth() {
  return useQuery<HealthResponse>({
    queryKey: ['health'],
    queryFn: fetchHealth,
    refetchInterval: 30000, // Refresh every 30s
    staleTime: 10000,
  })
}
