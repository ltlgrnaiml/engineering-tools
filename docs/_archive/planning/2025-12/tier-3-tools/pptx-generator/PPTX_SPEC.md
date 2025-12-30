# Tier 3: PowerPoint Generator Tool Specification

**Document Type:** Tool Specification  
**Audience:** Engineers  
**Last Updated:** 2025-01-26

---

## Overview

The PowerPoint Generator (PPTX) creates professional reports from templates and DataSets. It accepts data from DAT and SOV tools, maps data to template shapes, and generates PowerPoint files.

---

## Responsibilities

1. **DataSet Selection** - Select input DataSets (from DAT, SOV, or manual upload)
2. **Template Selection** - Choose PowerPoint template
3. **Config Loading** - Load mapping configuration
4. **Data Mapping** - Map DataSet columns to template shapes
5. **Preview** - Preview slides before generation
6. **Render** - Generate final PowerPoint file
7. **Export** - Download or save generated report

---

## Migration Notes

The existing PowerPointGenerator project at `/Users/kalepook_ai/Coding/PowerPointGenerator` will be migrated to `apps/pptx-generator/`. Key changes:

1. Update imports to use `shared.contracts`
2. Add DataSet input support (in addition to CSV upload)
3. Integrate with artifact store for output
4. Add "receive from pipe" functionality

---

## Acceptance Criteria (PPTX)

### AC-PPTX1: DataSet Input

- [ ] Accept DataSet IDs via query parameter
- [ ] Accept DataSet IDs via API request body
- [ ] Accept multiple DataSets (raw + analysis)
- [ ] Fallback to CSV upload if no DataSet provided
- [ ] Show DataSet preview before mapping

### AC-PPTX2: Template Management

- [ ] List available templates
- [ ] Upload new templates
- [ ] Template validation (shape naming)
- [ ] Template preview

### AC-PPTX3: Configuration

- [ ] Load config from file (JSON/YAML)
- [ ] Save config for reuse
- [ ] Config specifies: template, mappings, options
- [ ] Default config for quick generation

### AC-PPTX4: Data Mapping

- [ ] Map DataSet columns to shape names
- [ ] Support table shapes (multi-row)
- [ ] Support chart shapes (data series)
- [ ] Support text shapes (single values)
- [ ] Validation of mapping completeness

### AC-PPTX5: Preview

- [ ] Preview mapped slides before render
- [ ] Show placeholder values with actual data
- [ ] Highlight unmapped shapes

### AC-PPTX6: Render

- [ ] Generate PowerPoint with progress
- [ ] Support cancellation
- [ ] Output saved to workspace
- [ ] Report registered in artifact store

### AC-PPTX7: Export

- [ ] Download generated file
- [ ] Save to specified location
- [ ] Track output in run metadata

---

## Code Map

### Backend Structure (After Migration)

```text
apps/pptx-generator/backend/
├── src/pptx_generator/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── deps.py
│   │   └── schemas.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── run_manager.py
│   │   └── config_loader.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── data_loader.py      # DataSet loading
│   │   ├── template_service.py
│   │   ├── mapping_service.py
│   │   └── render_service.py
│   ├── renderers/
│   │   ├── __init__.py
│   │   ├── table_renderer.py
│   │   ├── chart_renderer.py
│   │   └── text_renderer.py
│   └── models/
│       ├── __init__.py
│       └── config.py
└── main.py
```

### Key Functions

#### `services/data_loader.py`

```python
async def load_datasets_for_report(
    dataset_ids: list[str],
) -> dict[str, tuple[pl.DataFrame, DataSetManifest]]:
    """Load multiple DataSets for report generation.
    
    Returns dict keyed by source tool (dat, sov) or dataset ID.
    """
```

#### `services/mapping_service.py`

```python
class MappingService:
    """Map DataSet columns to template shapes."""
    
    async def auto_map(
        self,
        datasets: dict[str, pl.DataFrame],
        template: Template,
    ) -> Mapping
    
    async def validate_mapping(
        self,
        mapping: Mapping,
        datasets: dict[str, pl.DataFrame],
        template: Template,
    ) -> list[ValidationError]
```

#### `services/render_service.py`

```python
async def render_presentation(
    template_path: Path,
    datasets: dict[str, pl.DataFrame],
    mapping: Mapping,
    config: RenderConfig,
    progress_callback: Callable[[float], None],
    cancel_token: CancelToken,
) -> Path:
    """Render final PowerPoint file."""
```

---

## API Endpoints

### Runs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/runs` | POST | Create new run |
| `/v1/runs` | GET | List runs |
| `/v1/runs/{id}` | GET | Get run details |
| `/v1/runs/{id}` | DELETE | Delete run |

### Templates

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/templates` | GET | List templates |
| `/v1/templates` | POST | Upload template |
| `/v1/templates/{id}` | GET | Get template details |
| `/v1/templates/{id}/shapes` | GET | List shapes in template |

### Mapping & Render

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/runs/{id}/mapping` | GET | Get current mapping |
| `/v1/runs/{id}/mapping` | PUT | Update mapping |
| `/v1/runs/{id}/mapping/auto` | POST | Auto-generate mapping |
| `/v1/runs/{id}/preview` | GET | Preview slides |
| `/v1/runs/{id}/render` | POST | Start render |
| `/v1/runs/{id}/render` | GET | Get render status |
| `/v1/runs/{id}/download` | GET | Download output |

---

## Data Flow

```text
DataSet(s)          Template          Config
    │                   │                │
    ▼                   ▼                ▼
┌─────────────────────────────────────────────────┐
│              Data Loader                         │
│  - Load DataSets from artifact store             │
│  - Support multiple DataSets (raw, sov)          │
│  - Merge/join if configured                      │
└─────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│              Mapping Service                     │
│  - Map columns to shapes                         │
│  - Validate completeness                         │
│  - Auto-map by naming convention                 │
└─────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│              Render Service                      │
│  - Apply data to template                        │
│  - Tables, charts, text                          │
│  - Progress tracking                             │
└─────────────────────────────────────────────────┘
                        │
                        ▼
               report.pptx
           (saved to workspace)
```

---

## Multi-DataSet Support

### Scenario: Raw + SOV Data

When PPTX receives both raw data (from DAT) and analysis results (from SOV):

```python
# Input datasets
datasets = {
    "dat": (raw_df, raw_manifest),      # Original aggregated data
    "sov": (sov_df, sov_manifest),      # ANOVA results
}

# Mapping config specifies which dataset each shape uses
mapping = {
    "raw_data_table": {"dataset": "dat", "columns": ["lot", "wafer", "cd_mean"]},
    "sov_chart": {"dataset": "sov", "columns": ["factor", "variance_pct"]},
    "summary_text": {"dataset": "sov", "value": "total_variance"},
}
```

---

## Change Order

### Phase 2A: Migration Prep (Week 2)

1. Create `apps/pptx-generator/` structure
2. Copy existing backend code
3. Update imports for shared contracts
4. Verify existing tests pass

### Phase 2B: DataSet Integration (Week 2-3)

1. Add `data_loader.py` for DataSet support
2. Update API to accept `input_datasets` parameter
3. Support multiple DataSets
4. Add query param handling for piping

### Phase 2C: Artifact Store Integration (Week 3)

1. Save outputs to workspace
2. Register reports in artifact store
3. Add lineage (parent DataSet IDs)

### Phase 2D: Frontend Updates (Week 3)

1. Add DataSetPicker integration
2. Show DataSet preview
3. Handle piped input via query params

---

## Validation Plan

### Unit Tests

- [ ] DataSet loading (single and multiple)
- [ ] Mapping validation
- [ ] Renderer output correctness

### Integration Tests

- [ ] Full run with DataSet input
- [ ] Full run with CSV upload (legacy)
- [ ] Multi-DataSet mapping

### E2E Tests

- [ ] Receive piped DataSet from DAT
- [ ] Generate report with SOV data
- [ ] Download generated file

---

## ADR References

| ADR | Application in PPTX |
|-----|---------------------|
| ADR-0002 | Preserve outputs on cancel |
| ADR-0005 | Deterministic run IDs |
| ADR-0009 | Timestamps in report metadata |
| ADR-0014 | Render cancellation semantics |
