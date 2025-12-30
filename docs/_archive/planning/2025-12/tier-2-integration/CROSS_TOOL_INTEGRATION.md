# Tier 2: Cross-Tool Integration

**Document Type:** Integration Specification  
**Audience:** Senior Engineers  
**Last Updated:** 2025-01-26

---

## Overview

This document defines how tools communicate and share data through the DataSet abstraction and Pipeline orchestration.

---

## DataSet: Universal Data Currency

### Concept

A **DataSet** is the universal data format that flows between tools. Every tool that produces data outputs a DataSet; every tool that consumes data accepts DataSets.

### Structure

```text
workspace/datasets/{dataset_id}/
├── data.parquet      # Main data table (Polars/PyArrow)
└── manifest.json     # Schema, provenance, lineage
```

### Manifest Schema

Reference: `shared/contracts/core/dataset.py::DataSetManifest`

Key fields for integration:

- **`dataset_id`**: Deterministic hash (per ADR-0005)
- **`created_by_tool`**: Source tool (`dat`, `sov`, `pptx`)
- **`parent_dataset_ids`**: Lineage tracking for piped data
- **`aggregation_levels`**: DAT-specific (e.g., `["wafer", "lot"]`)
- **`analysis_type`**: SOV-specific (e.g., `"anova"`)

### DataSet Lifecycle

```text
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Created   │────▶│   Active    │────▶│   Locked    │
│  (by tool)  │     │ (editable)  │     │ (immutable) │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Unlocked   │ (preserved, per ADR-0002)
                    └─────────────┘
```

---

## Data Piping Workflows

### Workflow 1: DAT → PPTX (Direct)

```text
User Flow:
1. Open Data Aggregator
2. Select source files
3. Configure aggregation levels (wafer, lot, product)
4. Parse and export → Creates DataSet ds_raw
5. Click "Pipe To" → Select "PowerPoint Generator"
6. PPTX opens with ds_raw pre-loaded
7. Load config file (defaults)
8. Generate report
```

API Sequence:

```text
POST /api/dat/v1/runs/{run_id}/export
  Response: { dataset_id: "ds_abc123", ... }

GET /api/pptx?input_datasets=ds_abc123
  (Frontend navigation with query param)

POST /api/pptx/v1/runs
  Body: { input_datasets: ["ds_abc123"], config_id: "default" }
```

### Workflow 2: DAT → SOV → PPTX (Pipeline)

```text
User Flow:
1. Open Data Aggregator
2. Select source files, configure, export → DataSet ds_raw
3. Click "Pipe To" → Select "SOV Analyzer"
4. SOV opens with ds_raw pre-loaded
5. Configure ANOVA (factors, response columns)
6. Run analysis → Creates DataSet ds_sov
7. Click "Pipe To" → Select "PowerPoint Generator"
8. PPTX opens with BOTH ds_raw and ds_sov
9. Load SOV report config
10. Map data to slides (raw in tables, SOV in charts)
11. Generate report
```

API Sequence:

```text
POST /api/dat/v1/runs/{run_id}/export
  Response: { dataset_id: "ds_raw_123", ... }

POST /api/sov/v1/analysis
  Body: { 
    input_datasets: ["ds_raw_123"],
    factors: ["lot", "wafer", "tool"],
    response_columns: ["cd_mean", "cd_sigma"]
  }
  Response: { dataset_id: "ds_sov_456", ... }

POST /api/pptx/v1/runs
  Body: { 
    input_datasets: ["ds_raw_123", "ds_sov_456"],
    config_id: "sov_report_template"
  }
```

---

## Pipeline Orchestration

### Pipeline Definition

Pipelines enable multi-step workflows to be defined and executed automatically.

Reference: `shared/contracts/core/pipeline.py::Pipeline`

Example Pipeline:

```json
{
  "pipeline_id": "pipe_abc123",
  "name": "Full SOV Analysis Report",
  "steps": [
    {
      "step_index": 0,
      "step_type": "dat:aggregate",
      "config": {
        "source_files": ["lot_data.csv"],
        "aggregation_levels": ["wafer", "lot"]
      }
    },
    {
      "step_index": 1,
      "step_type": "sov:anova",
      "input_dataset_ids": ["$step_0_output"],
      "config": {
        "factors": ["lot", "wafer"],
        "response_columns": ["cd_mean"]
      }
    },
    {
      "step_index": 2,
      "step_type": "pptx:generate",
      "input_dataset_ids": ["$step_0_output", "$step_1_output"],
      "config": {
        "template_id": "sov_report",
        "auto_generate": true
      }
    }
  ]
}
```

### Dynamic Input Resolution

The `$step_N_output` syntax allows steps to reference outputs from previous steps:

- `$step_0_output` → Resolves to the `output_dataset_id` of step 0
- Multiple references allowed: `["$step_0_output", "$step_1_output"]`

### Pipeline Execution States

```text
draft → queued → running → completed
                    ↓
                  failed
                    ↓
                cancelled (preserves completed artifacts)
```

### Cancellation Semantics (per ADR-0014)

When a pipeline is cancelled:

1. Current step is marked `cancelled`
2. Remaining steps are marked `skipped`
3. **All completed artifacts are preserved**
4. No partial data from cancelled step is persisted

---

## Gateway Cross-Tool APIs

### DataSet APIs (`/api/datasets/v1/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | List all DataSets (filterable by tool) |
| `/{id}` | GET | Get DataSet manifest |
| `/{id}/preview` | GET | Preview first N rows |
| `/{id}/lineage` | GET | Get parent/child relationships |

### Pipeline APIs (`/api/pipelines/v1/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | POST | Create new pipeline |
| `/` | GET | List all pipelines |
| `/{id}` | GET | Get pipeline details |
| `/{id}/execute` | POST | Start pipeline execution |
| `/{id}/cancel` | POST | Cancel running pipeline |

---

## Shared UI Components

### DataSetPicker

Used by all tools to select input DataSets.

Location: `shared/frontend/src/components/DataSetPicker.tsx`

Props:

- `onSelect: (datasetIds: string[]) => void`
- `multiSelect?: boolean` (default: false)
- `filterByTool?: "dat" | "sov" | "pptx"`

### PipeToButton

Appears after any tool's export stage.

Location: `shared/frontend/src/components/PipeToButton.tsx`

Props:

- `sourceDatasetId: string`
- `sourceTool: "dat" | "sov"`

Behavior:

1. Shows dialog with target tool options
2. Navigates to target tool with `?input_datasets={id}` query param
3. Target tool pre-populates DataSet selection

### DataSetCard

Displays DataSet summary in lists.

Location: `shared/frontend/src/components/DataSetCard.tsx`

Displays:

- Name and ID
- Source tool badge
- Row/column counts
- Created timestamp
- Parent count (lineage indicator)

---

## Acceptance Criteria (Integration)

### AC-I1: DataSet Interoperability

- [ ] DAT can export DataSet with proper manifest
- [ ] SOV can read DAT-produced DataSets
- [ ] PPTX can read DataSets from any tool
- [ ] Lineage is tracked when DataSet is derived from another

### AC-I2: Piping UX

- [ ] PipeToButton appears after export in DAT and SOV
- [ ] Target tool opens with DataSet pre-selected
- [ ] Multiple DataSets can be piped to PPTX

### AC-I3: Pipeline Execution

- [ ] Pipeline can be created with multiple steps
- [ ] Dynamic input resolution works (`$step_N_output`)
- [ ] Pipeline state is tracked in real-time
- [ ] Cancellation preserves completed work

### AC-I4: Gateway APIs

- [ ] `/api/datasets/v1/` lists DataSets from all tools
- [ ] `/api/pipelines/v1/` manages pipeline lifecycle
- [ ] Health check aggregates tool status

---

## Error Handling

### Missing DataSet

When a referenced DataSet is not found:

- API returns 404 with `DataSet not found: {id}`
- UI shows "DataSet unavailable" with option to refresh

### Pipeline Step Failure

When a pipeline step fails:

- Step state set to `failed` with error message
- Pipeline state set to `failed`
- Completed artifacts preserved
- User can view error and restart from failed step (future)

### Tool Unavailable

When a target tool is unavailable:

- Health check returns `"unavailable"` for that tool
- PipeToButton disables that option
- Pipeline step fails with "Tool unavailable" error

---

## Next Steps

Proceed to Tier 3 for individual tool specifications:

- `tier-3-tools/homepage/HOMEPAGE_SPEC.md`
- `tier-3-tools/data-aggregator/DAT_SPEC.md`
- `tier-3-tools/pptx-generator/PPTX_SPEC.md`
- `tier-3-tools/sov-analyzer/SOV_SPEC.md`
