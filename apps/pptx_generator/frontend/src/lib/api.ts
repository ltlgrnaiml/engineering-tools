import axios from 'axios'
import type {
  EnvironmentProfile,
  MappingSuggestion,
  MappingManifest,
  FourBarsStatus,
  PlanArtifacts,
  DerivedRequirementsManifest,
  ContextMapping,
  MetricMapping,
} from '../types'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface ProjectCreate {
  name: string
  description?: string
}

export interface Project {
  id: string
  name: string
  description?: string
  status: string
  template_id?: string
  data_file_id?: string
  domain_knowledge_id?: string
  shape_map_id?: string
  asset_mapping_id?: string
  created_at: string
  updated_at: string
}

export interface Template {
  id: string
  project_id: string
  filename: string
  file_path: string
  file_size: number
  uploaded_at: string
}

export interface ShapeMap {
  id: string
  template_id: string
  shapes: ShapeInfo[]
  slide_count: number
  created_at: string
}

export interface ShapeInfo {
  shape_id: number
  name: string
  shape_type: string
  slide_index: number
  position: {
    left: number
    top: number
    width: number
    height: number
  }
  has_text: boolean
  has_table: boolean
  has_chart: boolean
}

export interface DataFile {
  id: string
  project_id: string
  filename: string
  file_path: string
  file_size: number
  file_type: string
  row_count: number
  column_names: string[]
  uploaded_at: string
}

export const api = {
  async getProjects(): Promise<Project[]> {
    const response = await apiClient.get('/projects')
    return response.data
  },

  async createProject(data: ProjectCreate): Promise<Project> {
    const response = await apiClient.post('/projects', data)
    return response.data
  },

  async getProject(projectId: string): Promise<Project> {
    const response = await apiClient.get(`/projects/${projectId}`)
    return response.data
  },

  async uploadTemplate(projectId: string, file: File): Promise<Template> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await apiClient.post(`/templates/${projectId}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  async parseTemplate(projectId: string): Promise<ShapeMap> {
    const response = await apiClient.post(`/templates/${projectId}/parse`)
    return response.data
  },

  async getShapeMap(projectId: string): Promise<ShapeMap> {
    const response = await apiClient.get(`/templates/${projectId}/shape-map`)
    return response.data
  },

  async uploadDataFile(projectId: string, file: File): Promise<DataFile> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await apiClient.post(`/data/${projectId}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  async getDataFile(projectId: string): Promise<DataFile> {
    const response = await apiClient.get(`/data/${projectId}/data-file`)
    return response.data
  },

  // Template parsing v2
  parseTemplateV2: async (projectId: string): Promise<{
    shapeMap: ShapeMap
    drm: DerivedRequirementsManifest
    warnings: string[]
  }> => {
    const response = await apiClient.post(`/templates/${projectId}/parse-v2`)
    return response.data
  },

  // Environment Profile
  createEnvironmentProfile: async (
    projectId: string,
    profile: Partial<EnvironmentProfile>
  ): Promise<EnvironmentProfile> => {
    const response = await apiClient.post(
      `/requirements/${projectId}/environment-profile`,
      profile
    )
    return response.data
  },

  // Mapping Suggestions
  suggestMappings: async (projectId: string): Promise<{
    context_suggestions: Record<string, MappingSuggestion>
    metrics_suggestions: Record<string, MappingSuggestion>
  }> => {
    const response = await apiClient.post(
      `/requirements/${projectId}/mappings/suggest`
    )
    return response.data
  },

  // Context Mappings
  saveContextMappings: async (
    projectId: string,
    mappings: ContextMapping[]
  ): Promise<MappingManifest> => {
    const response = await apiClient.post(
      `/requirements/${projectId}/mappings/context`,
      { mappings }
    )
    return response.data
  },

  // Metrics Mappings
  saveMetricsMappings: async (
    projectId: string,
    mappings: MetricMapping[]
  ): Promise<MappingManifest> => {
    const response = await apiClient.post(
      `/requirements/${projectId}/mappings/metrics`,
      { mappings }
    )
    return response.data
  },

  // Four Bars Validation
  getFourBarsStatus: async (projectId: string): Promise<FourBarsStatus> => {
    const response = await apiClient.get(
      `/requirements/${projectId}/validation/four-bars`
    )
    return response.data
  },

  // Plan Building
  buildPlan: async (projectId: string): Promise<PlanArtifacts> => {
    const response = await apiClient.post(
      `/requirements/${projectId}/plan/build`
    )
    return response.data
  },

  // Get Plan
  getPlan: async (projectId: string): Promise<PlanArtifacts> => {
    const response = await apiClient.get(
      `/requirements/${projectId}/plan`
    )
    return response.data
  },

  // Data Columns
  getDataColumns: async (projectId: string): Promise<string[]> => {
    const response = await apiClient.get(`/data/${projectId}/columns`)
    return response.data
  },

  // Column Preview
  getColumnPreview: async (
    projectId: string,
    columnName: string
  ): Promise<any> => {
    const response = await apiClient.get(
      `/data/${projectId}/columns/${encodeURIComponent(columnName)}/preview`
    )
    return response.data
  },

  // State Management - Rollback Support
  clearProjectState: async (
    projectId: string,
    stepName: string
  ): Promise<{
    project_id: string
    cleared_from: string
    artifacts_cleared: string[]
    new_status: string
  }> => {
    const response = await apiClient.delete(
      `/projects/${projectId}/state/${stepName}`
    )
    return response.data
  },

  // Generation
  generatePresentation: async (
    projectId: string,
    outputFilename?: string
  ): Promise<{
    id: string
    project_id: string
    status: string
    output_file_path?: string
    output_filename?: string
    error_message?: string
    created_at: string
    completed_at?: string
  }> => {
    const response = await apiClient.post('/generation', {
      project_id: projectId,
      output_filename: outputFilename,
    })
    return response.data
  },

  downloadPresentation: async (generationId: string): Promise<Blob> => {
    const response = await apiClient.get(`/generation/${generationId}/download`, {
      responseType: 'blob',
    })
    return response.data
  },

  // Config Defaults
  getConfigDefaults: async (): Promise<{
    context_mappings: any[]
    metrics_mappings: any[]
    project_name: string
    template_file?: string
    data_file?: string
  }> => {
    const response = await apiClient.get('/config/defaults')
    return response.data
  },

  applyDefaultsToProject: async (projectId: string): Promise<{
    message: string
    context_mappings_count: number
    metrics_mappings_count: number
    manifest?: MappingManifest
  }> => {
    const response = await apiClient.post(`/apply-defaults/${projectId}`)
    return response.data
  },

  // Separate defaults endpoints
  applyContextDefaults: async (projectId: string): Promise<{
    message: string
    context_mappings_count: number
    context_mappings: ContextMapping[]
  }> => {
    const response = await apiClient.post(`/apply-defaults/${projectId}/contexts`)
    return response.data
  },

  applyMetricDefaults: async (projectId: string): Promise<{
    message: string
    metrics_mappings_count: number
    metrics_mappings: MetricMapping[]
  }> => {
    const response = await apiClient.post(`/apply-defaults/${projectId}/metrics`)
    return response.data
  },

  applyAllDefaults: async (projectId: string): Promise<{
    message: string
    context_mappings_count: number
    metrics_mappings_count: number
    context_mappings: ContextMapping[]
    metrics_mappings: MetricMapping[]
  }> => {
    const response = await apiClient.post(`/apply-defaults/${projectId}/all`)
    return response.data
  },

  // Data Operations
  getDataFiles: async (projectId: string): Promise<{
    files: Array<{
      id: string
      filename: string
      row_count: number
      column_count: number
      columns: string[]
    }>
    count: number
  }> => {
    const response = await apiClient.get(`/data/${projectId}/files`)
    return response.data
  },

  deriveColumn: async (
    projectId: string,
    config: {
      source_column: string
      new_column_name: string
      derivation_type: 'regex' | 'expression' | 'lookup'
      pattern?: string
      expression?: string
      lookup_table?: Record<string, string>
    }
  ): Promise<{
    message: string
    new_column: string
    preview: Array<Record<string, any>>
    non_null_count: number
  }> => {
    const response = await apiClient.post(`/data/${projectId}/derive-column`, config)
    return response.data
  },

  joinFiles: async (
    projectId: string,
    config: {
      primary_file_id: string
      secondary_file_id: string
      join_type: 'left' | 'right' | 'inner' | 'outer'
      primary_column: string
      secondary_column: string
      columns_to_include?: string[]
    }
  ): Promise<{
    message: string
    result_row_count: number
    result_columns: string[]
    join_type: string
  }> => {
    const response = await apiClient.post(`/data/${projectId}/join`, config)
    return response.data
  },

  concatFiles: async (
    projectId: string,
    config: {
      file_ids: string[]
      axis?: number
    }
  ): Promise<{
    message: string
    result_row_count: number
    result_columns: string[]
    files_merged: number
  }> => {
    const response = await apiClient.post(`/data/${projectId}/concat`, config)
    return response.data
  },

  getDataPreview: async (
    projectId: string,
    rows?: number,
    columns?: string[]
  ): Promise<{
    rows: Array<Record<string, any>>
    total_rows: number
    total_columns: number
    columns: string[]
  }> => {
    const params = new URLSearchParams()
    if (rows) params.append('rows', rows.toString())
    if (columns) columns.forEach(c => params.append('columns', c))
    const response = await apiClient.get(`/data/${projectId}/preview?${params}`)
    return response.data
  },

  getColumnStats: async (
    projectId: string,
    columnName: string
  ): Promise<{
    column_name: string
    data_type: string
    non_null_count: number
    null_count: number
    unique_count: number
    sample_values: any[]
    min_value?: number
    max_value?: number
    mean_value?: number
    std_value?: number
  }> => {
    const response = await apiClient.get(
      `/data/${projectId}/column-stats/${encodeURIComponent(columnName)}`
    )
    return response.data
  },
}

export const configApi = {
  // Domain Config
  getConfig: async (): Promise<any> => {
    const response = await apiClient.get('/config')
    return response.data
  },

  getJobContexts: async (): Promise<{
    job_contexts: Array<{
      name: string
      key: string
      values: string[]
      aliases: Record<string, string>
    }>
    primary_job_context: string
  }> => {
    const response = await apiClient.get('/config/job-contexts')
    return response.data
  },

  getPlottingConfig: async (): Promise<{
    job_context_colors: Record<string, string>
    colormap: string
    figure_dpi: number
    use_fixed_y_ranges: boolean
    fixed_y_ranges: Record<string, number[]>
  }> => {
    const response = await apiClient.get('/config/plotting')
    return response.data
  },

  getMetricsConfig: async (): Promise<{
    canonical: string[]
    rename_map: Record<string, string>
  }> => {
    const response = await apiClient.get('/config/metrics')
    return response.data
  },

  saveConfigMappings: async (data: {
    context_mappings?: any[]
    metrics_mappings?: any[]
    filename?: string
    overwrite?: boolean
  }): Promise<{
    message: string
    filename: string
    filepath: string
    context_mappings_count: number
    metrics_mappings_count: number
  }> => {
    const response = await apiClient.post('/config/save', data)
    return response.data
  },

  listConfigFiles: async (): Promise<{
    files: Array<{
      name: string
      path: string
      size?: number
      modified?: string
    }>
    count: number
  }> => {
    const response = await apiClient.get('/config/list')
    return response.data
  },

  loadConfigFile: async (filename: string): Promise<{
    filename: string
    filepath: string
    config: any
    validation: {
      has_job_contexts: boolean
      has_metrics: boolean
      has_defaults: boolean
      has_test_defaults: boolean
      is_valid: boolean
      errors: string[]
    }
  }> => {
    const response = await apiClient.get(`/config/load/${encodeURIComponent(filename)}`)
    return response.data
  },

  saveFullConfig: async (data: {
    filename: string
    config: any
    overwrite?: boolean
  }): Promise<{
    message: string
    filename: string
    filepath: string
  }> => {
    const response = await apiClient.put('/config/save-full', data)
    return response.data
  },
}

// Preview API
export const previewApi = {
  getSlidePreview: async (projectId: string, slideIndex: number = 0): Promise<{
    project_id: string
    slide_index: number
    total_slides: number
    slide_width: number
    slide_height: number
    shapes_count: number
    shapes: Array<{
      name: string
      type: string
      left: number
      top: number
      width: number
      height: number
      has_text?: boolean
      text_preview?: string
      has_table?: boolean
      table_rows?: number
      table_cols?: number
      has_chart?: boolean
    }>
    data_preview?: {
      filename: string
      row_count: number
      columns: string[]
    }
    preview_available: boolean
  }> => {
    const response = await apiClient.get(`/preview/${projectId}/preview?slide_index=${slideIndex}`)
    return response.data
  },

  // Per ADR-0019: Fetch backend workflow FSM state
  getWorkflowState: async (projectId: string): Promise<{
    project_id: string
    current_step: string
    step_statuses: Record<string, string>
    can_generate: boolean
    validation_errors: string[]
  } | null> => {
    try {
      const response = await apiClient.get(`/projects/${projectId}/workflow-state`)
      return response.data
    } catch (error) {
      console.warn('Workflow state not available:', error)
      return null
    }
  },

  getGenerationSummary: async (projectId: string): Promise<{
    project_id: string
    project_name: string
    status: string
    ready_to_generate: boolean
    components: {
      template: {
        filename: string
        slides_count: number
        shapes_per_slide: number[]
      } | null
      data: {
        filename: string
        row_count: number
        column_count: number
      } | null
      mappings: {
        context_configured: boolean
        metrics_configured: boolean
      } | null
    }
    warnings: string[]
  }> => {
    const response = await apiClient.get(`/preview/${projectId}/preview/summary`)
    return response.data
  },
}
