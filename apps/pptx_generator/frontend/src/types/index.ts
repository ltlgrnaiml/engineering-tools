export interface Project {
  id: string
  name: string
  description?: string
  status: string
  template_id?: string
  drm_id?: string
  environment_profile_id?: string
  data_file_id?: string
  context_mappings_id?: string
  metrics_mappings_id?: string
  validation_report_id?: string
  plan_artifacts_id?: string
  shape_map_id?: string
  asset_mapping_id?: string
  mapping_suggestions_id?: string
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

export interface ShapeMap {
  id: string
  template_id: string
  shapes: ShapeInfo[]
  slide_count: number
  created_at: string
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

export interface DRMFile {
  id: string
  project_id: string
  filename: string
  file_path: string
  file_size: number
  columns: string[]
  row_count: number
  uploaded_at: string
}

export type WorkflowStep =
  | 'template'
  | 'parse_drm'
  | 'environment'
  | 'data'
  | 'suggest'
  | 'context_map'
  | 'metrics_map'
  | 'validate'
  | 'plan'
  | 'generate'

// DRM Types
export interface RequiredContext {
  name: string
  source_type?: 'column' | 'regex' | 'default'
  derivation_pattern?: string
  default_value?: string
  description?: string
}

export interface RequiredMetric {
  name: string
  aggregation_type?: 'mean' | 'median' | 'std' | 'min' | 'max' | 'sum' | 'count' | '3sigma'
  data_type?: string
  unit?: string
  description?: string
}

export interface RequiredDataLevel {
  renderer_class: string
  cardinality: 'one_row' | 'many_rows' | 'aggregated' | 'aggregated_or_raw'
  description?: string
}

export interface RequiredRenderer {
  renderer_type: string
  renderer_subtype: string
  shape_references: string[]
  count: number
}

export interface DerivedRequirementsManifest {
  id: string
  template_id: string
  required_contexts: RequiredContext[]
  required_metrics: RequiredMetric[]
  required_data_levels: RequiredDataLevel[]
  required_renderers: RequiredRenderer[]
  created_at: string
  version: string
}

// Mapping Types
export interface ContextMapping {
  context_name: string
  source_type: 'column' | 'regex' | 'default'
  source_column?: string
  regex_pattern?: string
  default_value?: string
  description?: string
}

export interface MetricMapping {
  metric_name: string
  source_column: string
  rename_to?: string
  aggregation_semantics: 'mean' | 'median' | 'std' | 'min' | 'max' | 'sum' | 'count' | '3sigma'
  data_type?: string
  unit?: string
  description?: string
}

export interface MappingSuggestion {
  target_name: string
  suggested_source: string
  source_type: 'column' | 'regex' | 'default'
  confidence_score: number
  reasoning: string
}

export interface CoverageReport {
  total_required: number
  mapped_count: number
  coverage_percentage: number
  missing_items: string[]
}

export interface MappingManifest {
  id: string
  project_id: string
  context_mappings: ContextMapping[]
  metrics_mappings: MetricMapping[]
  context_coverage?: CoverageReport
  metrics_coverage?: CoverageReport
  created_at: string
  updated_at: string
}

// Environment Profile Types
export interface JobContext {
  name: string
  key: string
  values: string[]
  aliases: Record<string, string | undefined>
}

export interface DataRoots {
  templates_root: string
  output_root: string
  dataagg_rel: string
}

export interface EnvironmentProfile {
  id: string
  project_id?: string
  name: string
  source: 'filesystem' | 'adls' | 'sql'
  roots: DataRoots
  job_context: JobContext
  encoding_policy: string[]
}

// Validation Types
export type ValidationStatus = 'green' | 'yellow' | 'red'

export interface ValidationWarning {
  severity: string
  message: string
  suggested_fix?: string
}

export interface BarStatus {
  status: ValidationStatus
  coverage_percentage: number
  missing_items: string[]
  warnings: ValidationWarning[]
}

export interface FourBarsStatus {
  required_context: BarStatus
  required_metrics: BarStatus
  required_data_levels: BarStatus
  required_renderers: BarStatus
  is_all_green: boolean
}

// Plan Artifacts Types
export interface LookupJSON {
  fs_root: string
  fs_dataagg: string
  job_context_folders: Record<string, string>
}

export interface RequestGraphPartition {
  run_key: string
  job_context_value: string
  file_paths: string[]
  deduped: boolean
}

export interface RequestGraph {
  partitions: RequestGraphPartition[]
  total_partitions: number
  deduped_count: number
}

export interface PlanManifest {
  drm_sha1: string
  mappings_sha1: string
  environment_sha1: string
  lookup_sha1: string
  request_graph_sha1: string
  code_version: string
  frozen_at: string
}

export interface PlanArtifacts {
  id: string
  project_id: string
  lookup: LookupJSON
  request_graph: RequestGraph
  manifest: PlanManifest
  created_at: string
}
