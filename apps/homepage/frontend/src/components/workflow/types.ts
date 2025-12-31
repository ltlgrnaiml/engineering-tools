export type ArtifactType = 'discussion' | 'adr' | 'spec' | 'plan' | 'contract'

export type ArtifactStatus = 'draft' | 'active' | 'deprecated' | 'superseded' | 'completed'

export type FileFormat = 'json' | 'markdown' | 'python' | 'unknown'

export interface ArtifactSummary {
  id: string
  type: ArtifactType
  title: string
  status: ArtifactStatus
  file_path: string
  file_format: FileFormat
  updated_date?: string
}

export interface ArtifactListResponse {
  items: ArtifactSummary[]
  total: number
}

export type WorkflowMode = 'manual' | 'ai_lite' | 'ai_full'

export type WorkflowScenario = 'new_feature' | 'bug_fix' | 'architecture_change' | 'enhancement' | 'data_structure'

export type WorkflowStage = 'discussion' | 'adr' | 'spec' | 'contract' | 'plan'

export interface WorkflowState {
  id: string
  mode: WorkflowMode
  scenario: WorkflowScenario
  title: string
  current_stage: WorkflowStage
  artifacts_created: string[]
  created_at: string
}

export interface GraphNode {
  id: string
  type: ArtifactType
  label: string
  status: ArtifactStatus
  file_path: string
}

export interface GraphEdge {
  source: string
  target: string
  relationship: string
}

export interface GraphResponse {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export interface PromptResponse {
  prompt: string
  target_type: ArtifactType
  context: Record<string, unknown>
}
