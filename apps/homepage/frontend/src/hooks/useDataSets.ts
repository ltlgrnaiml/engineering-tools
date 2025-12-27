import { useQuery } from '@tanstack/react-query'

export interface DataSetRef {
  dataset_id: string
  name: string
  created_at: string
  created_by_tool: 'dat' | 'sov' | 'pptx' | 'manual'
  row_count: number
  column_count: number
  parent_count: number
  size_bytes: number | null
}

interface UseDataSetsOptions {
  tool?: string
  limit?: number
}

async function fetchDatasets(options?: UseDataSetsOptions): Promise<DataSetRef[]> {
  const params = new URLSearchParams()
  if (options?.tool) params.set('tool', options.tool)
  if (options?.limit) params.set('limit', String(options.limit))

  const response = await fetch(`/api/datasets/v1/?${params}`)
  if (!response.ok) throw new Error('Failed to fetch datasets')
  return response.json()
}

export function useDataSets(options?: UseDataSetsOptions, enabled: boolean = true) {
  return useQuery<DataSetRef[]>({
    queryKey: ['datasets', options],
    queryFn: () => fetchDatasets(options),
    enabled,
  })
}

export function useDataSetPreview(datasetId: string, rows: number = 100) {
  return useQuery({
    queryKey: ['dataset-preview', datasetId, rows],
    queryFn: async () => {
      const response = await fetch(`/api/datasets/v1/${datasetId}/preview?rows=${rows}`)
      if (!response.ok) throw new Error('Failed to fetch preview')
      return response.json()
    },
    enabled: !!datasetId,
  })
}
