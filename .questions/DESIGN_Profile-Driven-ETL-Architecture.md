# Design Proposal: Profile-Driven ETL Architecture

**Date**: 2025-12-29  
**Status**: DRAFT - For Review  
**Scope**: DAT Profile Extraction Implementation  
**Related ADRs**: ADR-0012 (Profile-Driven Extraction), ADR-0004 (8-Stage Pipeline)

---

## Executive Summary

This document proposes a comprehensive architecture for implementing profile-driven data extraction in the Data Aggregator Tool (DAT). The design enables:

1. **Data Source Agnostic**: Same profile schema works across JSON, CSV, Excel, Parquet
2. **User Intent Agnostic**: Profiles encode domain knowledge, users just select files
3. **Power User Flexibility**: Full YAML control for developers/domain experts
4. **Curated End-User Experience**: Sensible defaults, guided workflows
5. **Corporate Governance**: Profiles can enforce rules, limits, and domain constraints

---

## Research Synthesis

### Industry Best Practices Incorporated

| Pattern | Source | How We Apply It |
|---------|--------|-----------------|
| **Declarative Configuration** | dbt | YAML profiles define WHAT to extract, not HOW |
| **Composable Pipelines** | Singer taps/targets | Adapters are composable, profiles are portable |
| **Metadata-Driven ETL** | dmk-airflow-etl | Profiles ARE the metadata that drives extraction |
| **Schema-on-Read** | Modern Data Lake | Raw data staged first, profile applied at parse |
| **Data Validation First** | Great Expectations | Stable columns, validation rules in profiles |
| **Incremental Extraction** | CDC patterns | Profile-defined extraction strategies |

### Key Insight: Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     PROFILE LAYER (SSoT)                        │
│  • What to extract (tables, columns, paths)                     │
│  • How to transform (strategies, mappings, normalization)       │
│  • What to validate (stable columns, constraints)               │
│  • How to present (outputs, UI hints)                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓ governs
┌─────────────────────────────────────────────────────────────────┐
│                     ADAPTER LAYER (HOW)                         │
│  • Format-specific I/O (JSON, CSV, Excel, Parquet)              │
│  • Streaming for large files                                    │
│  • Schema probing                                                │
│  • JSONPath/XPath execution                                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓ produces
┌─────────────────────────────────────────────────────────────────┐
│                     DATASET LAYER (OUTPUT)                      │
│  • Flat, tabular DataFrames                                     │
│  • Manifest with provenance                                     │
│  • Cross-tool compatibility                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Profile Schema: Comprehensive Feature Set

### 1. Core Metadata

```yaml
schema_version: "1.0.0"       # Profile schema version (for migrations)
version: 1                     # Profile content version

meta:
  profile_id: "unique-id"      # Deterministic ID (used in lineage)
  title: "Human Readable"
  description: "..."
  created_by: "author"
  created_at: "ISO-8601"
  modified_at: "ISO-8601"
  revision: 1
  hash: ""                     # Content hash (computed at runtime)
  
  # NEW: Governance metadata
  owner: "team@company.com"
  classification: "internal"   # public, internal, confidential
  domain: "metrology"          # Domain tag for filtering
  tags: ["cdsem", "cd-measurement", "sem"]
```

### 2. Datasource Configuration

```yaml
datasource:
  id: "source-identifier"
  label: "Human Readable Source Name"
  format: "json"               # json, csv, excel, parquet, xml
  
  # File matching predicates (composable)
  filters:
    type: "group"
    op: "AND"                  # AND, OR, NOT
    children:
      - type: "predicate"
        field: "filename"      # filename, extension, path, size, modified_date
        op: "endswith"         # equals, contains, startswith, endswith, matches, gt, lt
        value: ".json"
        case: "insensitive"
      - type: "predicate"
        field: "size"
        op: "lt"
        value: 104857600       # 100MB limit
  
  # Format-specific options
  options:
    json:
      allow_bom: true
      encoding: "utf-8"
      jsonpath_engine: "jsonpath-ng"  # or "jmespath"
    csv:
      delimiter: ","
      quotechar: '"'
      header_row: 0
      skip_rows: 0
      encoding: "utf-8"
    excel:
      sheet_selection: "all"   # all, first, by_name, by_pattern
      sheet_pattern: "Data*"
      header_row: 0
```

### 3. Population & Sampling Strategies

```yaml
population:
  default_strategy: "all"
  strategies:
    all:
      description: "Include all records"
    valid_only:
      description: "Exclude records with validation errors"
      exclude_rules:
        - column: "status"
          condition: "equals"
          value: "invalid"
    outliers_excluded:
      description: "Exclude statistical outliers"
      method: "iqr"            # iqr, zscore, percentile
      threshold: 1.5
      apply_to:
        - "cd_value"
        - "roughness"
    sample:
      description: "Random sample for preview"
      method: "random"         # random, first_n, stratified
      size: 1000
      seed: 42                 # For reproducibility
```

### 4. Context Extraction (Multi-Level)

```yaml
context_defaults:
  # Priority 4 (lowest): Static defaults
  defaults:
    jobname: "Unknown Job"
    facility: "FAB1"
  
  # Priority 3: Regex extraction from filename/path
  regex_patterns:
    - field: "lot_id"
      pattern: "(?P<lot_id>LOT[A-Z0-9]{6,10})"
      scope: "filename"        # filename, path, full_path
      required: true
      validation:
        format: "^LOT[A-Z0-9]+$"
        min_length: 9
        max_length: 13
      on_fail: "warn"          # warn, error, skip_file
    
    - field: "measurement_date"
      pattern: "(?P<date>[0-9]{8})"
      scope: "filename"
      transform: "parse_date"  # Built-in transformer
      transform_args:
        format: "%Y%m%d"
  
  # Priority 2: JSON/file content extraction
  content_patterns:
    - field: "tool_id"
      path: "$.metadata.tool.id"
      required: false
      default: "UNKNOWN"
  
  # Priority 1 (highest): User overrides in UI
  allow_user_override:
    - "jobname"
    - "lot_id"
    - "wafer_id"

contexts:
  - name: "run_context"
    level: "run"
    paths:
      - "$.metadata"
      - "$.run_info"
    key_map:
      LotID: "$.metadata.lot_id"
      WaferID: "$.metadata.wafer_id"
      RecipeName: "$.run_info.recipe.name"
    primary_keys: ["LotID", "WaferID"]
    
  - name: "image_context"
    level: "image"
    paths: ["$.images[*].metadata"]
    key_map:
      ImageName: "$.image_name"
      AcquisitionTime: "$.acquisition_time"
    primary_keys: ["ImageName"]
    time_fields:
      earliest: "$.acquisition_time"
      latest: "$.acquisition_time"
```

### 5. Table Extraction Strategies

```yaml
levels:
  - name: "run"
    apply_context: "run_context"
    tables:
      # Strategy 1: Flat Object → Single Row
      - id: "run_summary"
        label: "Run Summary"
        description: "High-level summary statistics"
        select:
          strategy: "flat_object"
          path: "$.summary"
          # Optional: nested object flattening
          flatten_nested: true
          flatten_separator: "_"  # summary.stats.mean → summary_stats_mean
        
        # Schema enforcement
        stable_columns:
          - "total_images"
          - "mean_cd"
          - "sigma_cd"
        stable_columns_mode: "warn"  # warn, error, ignore
        stable_columns_subset: true  # Allow extra columns
        
        # Optional column transformations
        column_transforms:
          - source: "mean_cd"
            target: "mean_cd_nm"
            transform: "unit_convert"
            args: { from: "um", to: "nm", factor: 1000 }
      
      # Strategy 2: Headers + Data Arrays → DataFrame
      - id: "run_statistics"
        label: "Run Statistics"
        select:
          strategy: "headers_data"
          path: "$.statistics"
          headers_key: "columns"
          data_key: "values"
          # Handle missing headers
          infer_headers: false
          default_headers: ["col1", "col2", "col3"]
      
      # Strategy 3: Array of Objects → DataFrame  
      - id: "measurements"
        label: "Measurements"
        select:
          strategy: "array_of_objects"
          path: "$.measurements[*]"
          # Optional: select specific fields
          fields: ["id", "value", "timestamp"]
      
      # Strategy 4: Repeat Over (Cartesian product)
      - id: "cd_by_site"
        label: "CD by Site"
        select:
          strategy: "headers_data"
          path: "$.sites[{site_index}].cd_data"
          headers_key: "headers"
          data_key: "rows"
          repeat_over:
            path: "$.sites"
            as: "site_index"
            # Inject context from parent
            inject_fields:
              site_id: "$.site_id"
              site_name: "$.name"
      
      # Strategy 5: Pivot/Unpivot
      - id: "parameters_long"
        label: "Parameters (Long Form)"
        select:
          strategy: "unpivot"
          path: "$.parameters"
          id_vars: ["sample_id", "timestamp"]
          value_vars: ["param_a", "param_b", "param_c"]
          var_name: "parameter"
          value_name: "value"
      
      # Strategy 6: Join multiple paths
      - id: "enriched_data"
        label: "Enriched Data"
        select:
          strategy: "join"
          left:
            path: "$.measurements[*]"
            key: "site_id"
          right:
            path: "$.site_metadata[*]"
            key: "id"
          how: "left"  # left, right, inner, outer
```

### 6. Transformations & Normalization

```yaml
transformations:
  # Global column renames
  column_renames:
    "CD (nm)": "cd_nm"
    "3Sigma": "three_sigma"
  
  # Type coercion
  type_coercion:
    - column: "measurement_date"
      to_type: "datetime"
      format: "%Y-%m-%d %H:%M:%S"
    - column: "lot_id"
      to_type: "string"
      strip: true
      uppercase: true
  
  # Calculated columns
  calculated_columns:
    - name: "cd_range"
      expression: "cd_max - cd_min"
    - name: "uniformity_pct"
      expression: "(sigma_cd / mean_cd) * 100"
      round_to: 2
  
  # Filter rows
  row_filters:
    - column: "status"
      op: "not_equals"
      value: "rejected"
    - column: "cd_value"
      op: "between"
      min: 0
      max: 1000

normalization:
  nan_values: ["N/A", "NA", "null", "-", "", "#N/A", "NaN"]
  nan_replacement: null  # or a specific value
  
  # Numeric handling
  numeric_coercion: true
  numeric_errors: "coerce"  # coerce (to NaN), raise, ignore
  
  # String handling  
  string_strip: true
  string_case: "preserve"  # preserve, upper, lower, title
  
  # Unit handling
  units_policy: "preserve"  # preserve, normalize, strip
  unit_mappings:
    "nm": { canonical: "nm", factor: 1 }
    "um": { canonical: "nm", factor: 1000 }
    "μm": { canonical: "nm", factor: 1000 }
```

### 7. Validation Rules

```yaml
validation:
  # Schema validation
  schema_rules:
    required_columns: ["lot_id", "wafer_id", "cd_value"]
    column_types:
      lot_id: "string"
      wafer_id: "string"  
      cd_value: "float"
    unique_columns: ["measurement_id"]
  
  # Value validation
  value_rules:
    - column: "cd_value"
      constraints:
        - type: "range"
          min: 0
          max: 500
          on_fail: "warn"
        - type: "not_null"
          on_fail: "error"
    
    - column: "lot_id"
      constraints:
        - type: "regex"
          pattern: "^LOT[A-Z0-9]+$"
          on_fail: "error"
  
  # Row-level validation
  row_rules:
    - name: "cd_consistency"
      expression: "cd_left > 0 AND cd_right > 0"
      on_fail: "warn"
      message: "CD values should be positive"
  
  # Aggregate validation
  aggregate_rules:
    - name: "min_row_count"
      type: "row_count"
      min: 1
      on_fail: "error"
      message: "At least one row required"
    
    - name: "unique_images"
      type: "unique_count"
      column: "image_id"
      min: 1
      on_fail: "warn"

  # Validation output
  on_validation_fail: "continue"  # continue, stop, quarantine
  quarantine_table: "validation_failures"
```

### 8. Output Configuration

```yaml
outputs:
  # Default exports (always included)
  defaults:
    - id: "summary_export"
      from_level: "run"
      from_tables: ["run_summary", "run_statistics"]
      include_context: true
      format: "parquet"  # parquet, csv, excel
  
  # Optional exports (user selects)
  optional:
    - id: "full_detail"
      from_level: "image"
      from_tables: ["image_measurements", "image_quality"]
      include_context: true
      description: "Full image-level detail data"
  
  # Aggregation outputs
  aggregations:
    - id: "lot_summary"
      from_table: "run_summary"
      group_by: ["lot_id"]
      aggregations:
        mean_cd: "mean"
        sigma_cd: "mean"
        total_images: "sum"
      output_table: "lot_aggregated"
  
  # Join outputs
  joins:
    - id: "enriched_export"
      left_table: "run_summary"
      right_table: "run_statistics"
      on: ["run_id"]
      how: "left"

  # File naming
  file_naming:
    template: "{profile_id}_{lot_id}_{timestamp}"
    timestamp_format: "%Y%m%d_%H%M%S"
    sanitize: true  # Remove invalid characters
```

### 9. UI Hints & Presentation

```yaml
ui:
  # Discovery stage hints
  discovery:
    show_file_preview: true
    max_preview_files: 10
    highlight_matching: true
  
  # Table selection hints
  table_selection:
    group_by_level: true
    default_selected:
      run: ["run_summary", "run_statistics"]
      image: ["image_measurements"]
    collapsed_by_default:
      - "diagnostics"
      - "psd_*"
  
  # Preview hints
  preview:
    max_rows: 100
    max_columns: 50
    column_width: "auto"  # auto, fixed, wrap
    number_format: "0.0000"
    date_format: "YYYY-MM-DD HH:mm:ss"
    null_display: "—"
  
  # Context stage hints
  context:
    show_regex_matches: true
    editable_fields: ["jobname", "lot_id"]
    readonly_fields: ["profile_id", "created_at"]
  
  # Export stage hints
  export:
    default_name_template: "{profile_title} - {lot_id}"
    show_row_count: true
    show_column_list: true
    allow_format_selection: true
    formats: ["parquet", "csv", "excel"]
  
  # Context application options (NEW - per context separation design)
  context_options:
    include_context_toggle: true  # Show context toggle checkboxes
    default_include_run_context: true
    default_include_image_context: false
```

### 9.1 Context Separation Architecture (IMPORTANT)

**Key Design Principle**: Raw data tables and context are kept SEPARATE during extraction. Users control context application at output time via simple checkboxes.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     EXTRACTION PHASE                                     │
│                                                                          │
│   ┌──────────────┐     ┌──────────────────────────────────────────┐     │
│   │  Raw Files   │────▶│           ProfileExecutor                 │     │
│   └──────────────┘     │                                          │     │
│                        │  Returns ExtractionResult:               │     │
│                        │  ├─ tables: Dict[table_id, DataFrame]    │     │
│                        │  │         (NO context columns)          │     │
│                        │  ├─ run_context: Dict[str, Any]          │     │
│                        │  │         {LotID, WaferID, ...}         │     │
│                        │  └─ image_contexts: Dict[image_id, Dict] │     │
│                        │            {ImageName, AcqTime, ...}     │     │
│                        └──────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     USER SELECTION PHASE                                 │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │  TABLE SELECTION                                [Context: ☑]    │   │
│   ├─────────────────────────────────────────────────────────────────┤   │
│   │  ▼ RUN LEVEL TABLES                                             │   │
│   │    ☑ Run Summary                                                │   │
│   │    ☑ Run Statistics                                             │   │
│   │    ☐ CD by Site                                                 │   │
│   │                                                                 │   │
│   │  ▼ IMAGE LEVEL TABLES                                           │   │
│   │    ☑ Image Measurements                                         │   │
│   │    ☐ Image Quality                                              │   │
│   │                                                                 │   │
│   │  ─────────────────────────────────────────────────────────────  │   │
│   │  CONTEXT OPTIONS                                                │   │
│   │    ☑ Apply run-level context (LotID, WaferID, RecipeName...)   │   │
│   │    ☐ Apply image-level context (ImageName, AcquisitionTime...) │   │
│   └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     OUTPUT PHASE                                         │
│                                                                          │
│   OutputBuilder.build_outputs(                                          │
│       extracted_tables=result.tables,                                   │
│       run_context=result.run_context,                                   │
│       image_contexts=result.image_contexts,                             │
│       context_options=ContextOptions(                                   │
│           include_run_context=True,    # User checked this             │
│           include_image_context=False, # User unchecked this           │
│       )                                                                 │
│   )                                                                     │
│                                                                          │
│   Result: Tables WITH context columns per user selection                │
└─────────────────────────────────────────────────────────────────────────┘
```

**API Endpoints**:

```python
# 1. Extract tables and context (separately)
POST /api/dat/runs/{run_id}/stages/parse/profile-extract
Response:
{
    "tables_extracted": 5,
    "table_details": {...},  # Raw tables without context
    "context": {
        "run_context": {"LotID": "LOT123", "WaferID": "W01", ...},
        "image_contexts": {"IMG_001": {"ImageName": "...", ...}},
        "available_run_keys": ["LotID", "WaferID", "RecipeName"],
        "available_image_keys": ["ImageName", "AcquisitionTime"]
    }
}

# 2. Apply context to tables (user-controlled)
POST /api/dat/runs/{run_id}/stages/parse/apply-context
Request:
{
    "include_run_context": true,
    "include_image_context": false,
    "run_context_keys": ["LotID", "WaferID"],  # Optional: specific keys only
    "table_ids": ["run_summary", "run_statistics"]  # Optional: specific tables
}
Response:
{
    "tables": {...},  # Tables with context columns added
    "context_applied": {
        "run_context_keys": ["LotID", "WaferID"],
        "image_context_keys": []
    }
}
```

**Benefits**:
1. **User Control**: Simple checkboxes give users control over output structure
2. **Flexibility**: Same extraction, different outputs based on user needs
3. **Efficiency**: Context computed once, applied as needed
4. **Transparency**: Users see exactly what context will be added

### 10. Governance & Limits

```yaml
governance:
  # Access control
  access:
    read: ["all"]
    modify: ["admin", "data-engineers"]
    delete: ["admin"]
  
  # Audit trail
  audit:
    log_access: true
    log_modifications: true
    retention_days: 365
  
  # Compliance
  compliance:
    data_classification: "internal"
    pii_columns: []
    mask_in_preview: []

overrides:
  # What users CAN override
  allow:
    context_values: true
    table_selection: true
    output_format: true
    population_strategy: true
  
  # What users CANNOT override  
  deny:
    extraction_paths: true
    validation_rules: false
    normalization: false

limits:
  # Resource limits
  max_files_per_run: 1000
  max_file_size_mb: 500
  max_total_size_gb: 10
  max_rows_output: 10000000
  
  # Complexity limits
  max_tables_per_level: 50
  max_columns_per_table: 500
  max_predicates: 20
  max_regex_length: 256
  max_jsonpath_depth: 10
  
  # Time limits
  parse_timeout_seconds: 3600
  preview_timeout_seconds: 30
```

---

## Implementation Architecture

### Phase 1: Profile Executor Engine

The core component that interprets profiles and executes extraction:

```
┌─────────────────────────────────────────────────────────────────┐
│                     ProfileExecutor                             │
├─────────────────────────────────────────────────────────────────┤
│ + execute(profile: DATProfile, files: List[Path]) → DataFrame  │
│ + extract_context(profile, file) → Dict                        │
│ + extract_tables(profile, file, context) → Dict[str, DataFrame]│
│ + apply_transformations(df, transforms) → DataFrame            │
│ + validate(df, rules) → ValidationResult                       │
│ + aggregate(dfs, config) → DataFrame                           │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
    ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
    │ JSONAdapter │   │ CSVAdapter  │   │ ExcelAdapter│
    └─────────────┘   └─────────────┘   └─────────────┘
```

### Phase 2: Strategy Pattern for Extraction

```python
# Extraction strategies as pluggable components
class ExtractionStrategy(Protocol):
    def extract(self, data: Any, config: dict) -> pl.DataFrame: ...

class FlatObjectStrategy(ExtractionStrategy):
    """Extract flat JSON object as single-row DataFrame."""
    
class HeadersDataStrategy(ExtractionStrategy):
    """Extract headers + data arrays as DataFrame."""
    
class ArrayOfObjectsStrategy(ExtractionStrategy):
    """Extract array of objects as DataFrame."""
    
class RepeatOverStrategy(ExtractionStrategy):
    """Extract with iteration over array elements."""
```

### Phase 3: Integration Points

```
DAT Pipeline Stages          Profile Usage
─────────────────────        ────────────────────────────────
DISCOVERY                →   datasource.filters (file matching)
SELECTION                →   datasource.options (format hints)
CONTEXT                  →   context_defaults, contexts
TABLE_SELECTION          →   levels[].tables, ui.table_selection
PREVIEW                  →   ui.preview, population.sample
PARSE                    →   **FULL PROFILE EXECUTION**
EXPORT                   →   outputs, governance.limits
```

---

## Migration Path

### Current State → Target State

| Aspect | Current | Target |
|--------|---------|--------|
| Parse Stage | Reads raw files via adapters | Executes profile extraction strategies |
| Context | User enters manually | Auto-extracted via regex + JSONPath |
| Tables | File = Table | JSONPath paths = Tables |
| Preview | Raw data | Extracted + transformed data |
| Output | Nested objects | Flat, columnar data |

### Implementation Milestones

1. **M1**: Profile Executor Core (FlatObject, HeadersData strategies)
2. **M2**: Context Auto-Extraction (regex, JSONPath)  
3. **M3**: Validation Engine Integration
4. **M4**: Transform Pipeline (renames, calculated columns)
5. **M5**: UI Integration (preview, table selection from profile)
6. **M6**: Aggregation & Join Outputs

---

## Design Decisions Required

### D1: JSONPath Engine

**Options**:
- A) `jsonpath-ng` (Python, well-maintained)
- B) `jmespath` (AWS standard, powerful)
- C) Support both (profile selects engine)

**Recommendation**: Option C - JMESPath for complex queries, JSONPath for simple paths.

### D2: Profile Storage

**Options**:
- A) YAML files in repo (current)
- B) Database storage with CRUD API
- C) Hybrid (builtin in repo, custom in DB)

**Recommendation**: Option C - Builtin profiles versioned with code, user profiles in DB.

### D3: Schema Evolution

**Options**:
- A) Strict versioning (breaking changes = new profile)
- B) Migration scripts (auto-upgrade profiles)
- C) Forward-compatible schema (ignore unknown fields)

**Recommendation**: Option C with validation warnings for unknown fields.

---

## Alignment with Existing ADRs

| ADR | How This Design Aligns |
|-----|------------------------|
| ADR-0004 | Profile execution slots into 8-stage pipeline |
| ADR-0012 | This IS the implementation of profile-driven extraction |
| ADR-0005 | Content-addressed IDs from profile + inputs |
| ADR-0009 | ISO-8601 timestamps, provenance in manifest |
| ADR-0015 | Output always Parquet, optional CSV/Excel |
| ADR-0018 | Path safety enforced, deterministic execution |
| ADR-0036 | Validation rules generate test cases |

---

## Next Steps

1. **Review this design** - Identify gaps or changes
2. **Prioritize features** - Which capabilities are MVP?
3. **Create implementation plan** - Milestone breakdown
4. **Update ADR-0012** - Add concrete implementation details
5. **Create SPEC-DAT-PROFILE** - Formal profile schema spec

---

*Design document prepared for review*
