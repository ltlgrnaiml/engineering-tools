export type ArtifactType = 'discussion' | 'adr' | 'spec' | 'plan' | 'contract'

export type ArtifactStatus = 'draft' | 'active' | 'deprecated' | 'superseded' | 'completed'

export interface ArtifactSummary {
  id: string
  type: ArtifactType
  title: string
  status: ArtifactStatus
  file_path: string
  updated_date?: string
}

export interface ArtifactListResponse {
  items: ArtifactSummary[]
  total: number
}
