# SPEC Index: Engineering Tools Platform

> **Tier 2 Documents**: SPECs define WHAT is being built (implementation details, APIs, schemas).
> They link upward to ADRs (WHY) and downward to Tier-0 Contracts (SOURCE OF TRUTH).

## SPEC Hierarchy

```
Tier 0: Contracts (Pydantic in shared/contracts/) - SOURCE OF TRUTH
  ↑ (references)
Tier 2: SPECs (WHAT) - This tier
  ↑ (implements)
Tier 1: ADRs (WHY)
```

## SPEC Registry

### Core SPECs (Platform-Wide)

| SPEC ID | Title | Implements ADR | Tier-0 Contracts |
|---------|-------|----------------|------------------|
| SPEC-0001 | Stage Orchestration State Machine | ADR-0001 | `shared/contracts/core/pipeline.py` |
| SPEC-0008 | Contract Discipline API | ADR-0016 | `shared/contracts/__init__.py` |
| SPEC-0009 | Engineering Docs Tenets | ADR-0010, ADR-0015, ADR-0017 | `shared/contracts/adr_schema.py` |
| SPEC-0010 | Contract Drift Type Coverage | ADR-0009 | - (CI tooling) |
| SPEC-0011 | Concurrency Determinism | ADR-0012 | `shared/contracts/core/concurrency.py` |
| SPEC-0012 | Audit Trail Enforcement | ADR-0008 | `shared/contracts/core/audit.py` |
| SPEC-0013 | Artifact Lifecycle Preservation | ADR-0002 | `shared/contracts/core/artifact_registry.py` |
| SPEC-0016 | Path Safety And Normalization | ADR-0017#path-safety | `shared/contracts/core/path_safety.py` |
| SPEC-0019 | Cross-Platform Shell Execution | ADR-0012 | `shared/contracts/core/concurrency.py` |
| SPEC-0028 | DataSet Lineage | ADR-0025 | `shared/contracts/core/dataset.py` |
| SPEC-0029 | Pipeline Execution | ADR-0026 | `shared/contracts/core/pipeline.py` |
| **SPEC-0031** | **Unified Rendering Contracts** | **ADR-0028** | `shared/contracts/core/rendering.py` |
| **SPEC-0032** | **Rendering Engine Architecture** | **ADR-0028** | `shared/rendering/` |
| **SPEC-0033** | **Output Target Adapters** | **ADR-0028** | `shared/rendering/adapters/` |

### DAT SPECs (Data Aggregation Tool)

| SPEC ID | Title | Implements ADR | Tier-0 Contracts |
|---------|-------|----------------|------------------|
| SPEC-0001 | Stage Orchestration State Machine | ADR-0001-DAT | `shared/contracts/dat/stage.py` (NEW) |
| SPEC-0002 | Profile Context Orchestration | ADR-0003, ADR-0011 | `shared/contracts/dat/profile.py` (NEW) |
| SPEC-0003 | Frontend Panel Status Integration | ADR-0003, ADR-0006 | `shared/contracts/dat/panel_status.py` (NEW) |
| SPEC-0004 | Profile Driven Extraction | ADR-0011, ADR-0014 | `shared/contracts/dat/profile.py` (NEW) |
| SPEC-0005 | Message Catalog | ADR-0010, ADR-0011 | `shared/contracts/messages/catalog.py` (NEW) |
| SPEC-0006 | Table Availability Status | ADR-0006 | `shared/contracts/dat/table_status.py` (NEW) |
| SPEC-0007 | Stable Columns Policy | ADR-0011 | `shared/contracts/dat/columns.py` (NEW) |
| SPEC-0014 | Deterministic Stage ID | ADR-0004-DAT | `shared/contracts/core/id_generator.py` (NEW) |
| SPEC-0015 | Cancellation Cleanup | ADR-0013 | `shared/contracts/dat/cancellation.py` (NEW) |

### PPTX SPECs (PowerPoint Generator)

| SPEC ID | Title | Implements ADR | Tier-0 Contracts |
|---------|-------|----------------|------------------|
| SPEC-0019 | PPTX Template Schema | ADR-0018 | `shared/contracts/pptx/template.py` (NEW) |
| SPEC-0020 | PPTX Shape Discovery | ADR-0018 | `shared/contracts/pptx/shape.py` (NEW) |
| SPEC-0021 | PPTX Workflow FSM | ADR-0019 | `shared/contracts/pptx/workflow.py` (NEW) |
| SPEC-0022 | PPTX Domain Config Schema | ADR-0020 | `shared/contracts/pptx/domain.py` (NEW) |
| SPEC-0023 | PPTX Renderer Interface | ADR-0021 | `shared/contracts/pptx/renderer.py` (NEW) |

### SOV SPECs (Source of Variance Analyzer)

| SPEC ID | Title | Implements ADR | Tier-0 Contracts |
|---------|-------|----------------|------------------|
| SPEC-0024 | SOV ANOVA Computation | ADR-0022 | `shared/contracts/sov/anova.py` (NEW) |
| SPEC-0025 | SOV Pipeline Stages | ADR-0022 | `shared/contracts/sov/pipeline.py` (NEW) |
| SPEC-0026 | SOV DataSet IO | ADR-0023 | `shared/contracts/sov/dataset_io.py` (NEW) |
| SPEC-0027 | SOV Visualization Contracts | ADR-0024 | `shared/contracts/sov/visualization.py` (NEW) |

### DevTools SPECs

| SPEC ID | Title | Implements ADR | Tier-0 Contracts |
|---------|-------|----------------|------------------|
| SPEC-0030 | DevTools API | ADR-0027 | `shared/contracts/devtools/api.py` (NEW) |

## Tier-0 Contract Status

### Core Contracts ✓

| Contract | Location | Key Classes | Used By |
|----------|----------|-------------|---------|
| ADRSchema | `shared/contracts/adr_schema.py` | ADRSchema, Provenance | SPEC-0009 |
| Pipeline | `shared/contracts/core/pipeline.py` | Pipeline, PipelineStep, PipelineStepState | SPEC-0001, SPEC-0029 |
| DataSet | `shared/contracts/core/dataset.py` | DataSetManifest, ColumnMeta, DataSetRef | SPEC-0028 |
| ArtifactRegistry | `shared/contracts/core/artifact_registry.py` | ArtifactRecord, ArtifactQuery | SPEC-0013 |
| Audit | `shared/contracts/core/audit.py` | AuditTimestamp, AuditTrail, LifecycleEvent, TimestampMixin | SPEC-0012 |
| PathSafety | `shared/contracts/core/path_safety.py` | RelativePath, WorkspacePath, PathValidationError | SPEC-0016 |
| Concurrency | `shared/contracts/core/concurrency.py` | PlatformInfo, ConcurrencyConfig, OSType, ShellType | SPEC-0011, SPEC-0019 |
| **Rendering** | `shared/contracts/core/rendering.py` | RenderSpec, ChartSpec, TableSpec, RenderStyle, DataSeries, OutputTarget | SPEC-0031, SPEC-0032, SPEC-0033 |
| **IDGenerator** | `shared/contracts/core/id_generator.py` | IDConfig, compute_deterministic_id, StageIDInputs, UploadStageInputs, ParseStageInputs | SPEC-0014 |

### DAT Contracts ✓

| Contract | Location | Key Classes | Used By |
|----------|----------|-------------|---------|
| **Stage** | `shared/contracts/dat/stage.py` | DATStageState, DATStageConfig, DATStageResult, ParseStageConfig, AggregateStageConfig, ExportStageConfig | SPEC-0001 |
| **Profile** | `shared/contracts/dat/profile.py` | ExtractionProfile, ColumnMapping, AggregationRule, FilePattern, ValidationRule | SPEC-0002, SPEC-0004 |
| **TableStatus** | `shared/contracts/dat/table_status.py` | TableAvailability, TableAvailabilityStatus, TableStatusReport, TableHealth | SPEC-0006 |
| **Cancellation** | `shared/contracts/dat/cancellation.py` | CancellationRequest, CancellationResult, Checkpoint, CheckpointRegistry, CleanupRequest, CancellationAuditLog | SPEC-DAT-0015 |

### PPTX Contracts ✓

| Contract | Location | Key Classes | Used By |
|----------|----------|-------------|---------|
| **Template** | `shared/contracts/pptx/template.py` | PPTXTemplate, SlideTemplate, SlideLayout, RenderConfig, RenderResult | SPEC-0019, SPEC-0021 |
| **Shape** | `shared/contracts/pptx/shape.py` | ShapeDiscoveryResult, ShapePlaceholder, ShapeBinding, TextConfig, TableConfig, ChartConfig, ImageConfig | SPEC-0020, SPEC-0023 |

### SOV Contracts ✓

| Contract | Location | Key Classes | Used By |
|----------|----------|-------------|---------|
| **ANOVA** | `shared/contracts/sov/anova.py` | ANOVAConfig, ANOVAResult, FactorEffect, VarianceComponent, PostHocResult | SPEC-0024, SPEC-0025 |
| **Visualization** | `shared/contracts/sov/visualization.py` | VisualizationSpec, VisualizationType, BoxPlotConfig, InteractionPlotConfig, PlotStyle | SPEC-0027 |

### Messages Contracts ✓

| Contract | Location | Key Classes | Used By |
|----------|----------|-------------|---------|
| **Catalog** | `shared/contracts/messages/catalog.py` | MessageDefinition, MessageCatalog, ErrorMessage, ProgressMessage, ValidationMessage | SPEC-0005, ADR-0017#message-catalogs |

### DevTools Contracts ✓

| Contract | Location | Key Classes | Used By |
|----------|----------|-------------|---------|
| **API** | `shared/contracts/devtools/api.py` | DevToolsState, ADRListResponse, ADRSaveRequest, SchemaValidationRequest, APITestRequest | SPEC-0030 |

### Rendering Engine Implementation ✓

| Module | Location | Key Classes | Used By |
|--------|----------|-------------|---------|
| **Engine** | `shared/rendering/engine.py` | RenderEngine | SPEC-0032 |
| **Registry** | `shared/rendering/registry.py` | AdapterRegistry, get_adapter, register_adapter | SPEC-0033 |
| **BaseAdapter** | `shared/rendering/adapters/base.py` | BaseOutputAdapter, MatplotlibAdapterMixin | SPEC-0033 |
| **JSONAdapter** | `shared/rendering/adapters/json_adapter.py` | JSONAdapter | SPEC-0033 |

## Cross-Reference Validation

All ADRs must have:
1. `implementation_specs` field pointing to SPEC documents
2. SPECs must link to `tier_0_contracts` (Pydantic models)
3. Contracts are the single source of truth for data structures

---
*Last Updated: 2025-12-27*
*Maintainer: Mycahya Eggleston*
