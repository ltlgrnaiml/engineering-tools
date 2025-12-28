# SPEC Index: Engineering Tools Platform

> **Tier 2 Documents**: SPECs define WHAT is being built (implementation details, APIs, schemas).
> They link upward to ADRs (WHY) and downward to Tier-0 Contracts (SOURCE OF TRUTH).
>
> **Context**: Solo-dev, greenfield, AI-assisted development. SPECs aligned with simplified ADRs.

## SPEC Hierarchy

```text
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
| **SPEC-0028** | **DataSet Lineage & Versioning** *(updated)* | **ADR-0025** | `shared/contracts/core/dataset.py` |
| SPEC-0029 | Pipeline Execution | ADR-0026 | `shared/contracts/core/pipeline.py` |
| SPEC-0031 | Unified Rendering Contracts | ADR-0028 | `shared/contracts/core/rendering.py` |
| SPEC-0032 | Rendering Engine Architecture | ADR-0028 | `shared/rendering/` |
| SPEC-0033 | Output Target Adapters | ADR-0028 | `shared/rendering/adapters/` |
| **SPEC-0034** | **Simplified API Naming** *(updated)* | **ADR-0029** | - |
| SPEC-0035 | Error Response Implementation Guide | ADR-0031 | `shared/contracts/core/error_response.py` |
| SPEC-0036 | Idempotency Implementation Guide | ADR-0032 | `shared/contracts/core/idempotency.py` |

### Solo-Dev Optimization SPECs *(NEW)*

| SPEC ID | Title | Implements ADR | Tier-0 Contracts |
|---------|-------|----------------|------------------|
| **SPEC-0037** | **AI-Assisted Development Patterns** | **ADR-0033** | - (code conventions) |
| **SPEC-0038** | **Automated Documentation Pipeline** | **ADR-0034** | - (tooling) |
| **SPEC-0039** | **Contract-Driven Test Generation** | **ADR-0035** | - (testing) |
| **SPEC-0040** | **Observability & Tracing (Backend + Frontend)** | **ADR-0036** | `shared/contracts/core/logging.py`, `shared/contracts/core/frontend_logging.py` |
| **SPEC-0041** | **Development Environment Setup** | **ADR-0037** | - (scripts) |
| **SPEC-0042** | **CI/CD Pipeline Implementation** | **ADR-0038** | - (workflows) |
| **SPEC-0043** | **Deployment Infrastructure** | **ADR-0039** | - (Pulumi) |

### DAT SPECs (Data Aggregation Tool)

| SPEC ID | Title | Implements ADR | Tier-0 Contracts |
|---------|-------|----------------|------------------|
| SPEC-DAT-0001 | Stage Graph | ADR-0001-DAT | `shared/contracts/dat/stage.py` |
| SPEC-DAT-0002 | Profile Extraction | ADR-0003, ADR-0011 | `shared/contracts/dat/profile.py` |
| **SPEC-DAT-0003** | **Adapter Interface & Registry** | **ADR-0011** | `shared/contracts/dat/adapter.py` (NEW) |
| **SPEC-DAT-0004** | **Large File Streaming** | **ADR-0040** | `shared/contracts/dat/adapter.py` |
| **SPEC-DAT-0005** | **Profile File Management** | **ADR-0011, ADR-0027** | `shared/contracts/dat/profile.py` |
| SPEC-DAT-0006 | Table Availability Status | ADR-0006 | `shared/contracts/dat/table_status.py` |
| SPEC-DAT-0015 | Cancellation Cleanup | ADR-0013 | `shared/contracts/dat/cancellation.py` |

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
| **Logging** | `shared/contracts/core/logging.py` | LogEvent, RequestContext, StateSnapshot, FSMTransitionLog, ArtifactLog, TraceQuery, TraceResult | SPEC-0040 |
| **FrontendLogging** | `shared/contracts/core/frontend_logging.py` | FrontendLogEntry, FrontendAPICall, FrontendStateTransition, FrontendDebugExport, DebugPanelConfig | SPEC-0040 |

### DAT Contracts ✓

| Contract | Location | Key Classes | Used By |
|----------|----------|-------------|---------|
| **Stage** | `shared/contracts/dat/stage.py` | DATStageState, DATStageConfig, DATStageResult, ParseStageConfig, AggregateStageConfig, ExportStageConfig | SPEC-DAT-0001 |
| **Profile** | `shared/contracts/dat/profile.py` | ExtractionProfile, ColumnMapping, AggregationRule, FilePattern, ValidationRule | SPEC-DAT-0002, SPEC-DAT-0005 |
| **Adapter** | `shared/contracts/dat/adapter.py` (NEW) | BaseFileAdapter, AdapterMetadata, AdapterCapabilities, SchemaProbeResult, ReadOptions, StreamOptions | SPEC-DAT-0003, SPEC-DAT-0004 |
| **TableStatus** | `shared/contracts/dat/table_status.py` | TableAvailability, TableAvailabilityStatus, TableStatusReport, TableHealth | SPEC-DAT-0006 |
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

## Summary of Changes (2025-12-28)

### New SPECs (Solo-Dev Optimizations)

- **SPEC-0037**: AI-Assisted Development Patterns (implements ADR-0033)
- **SPEC-0038**: Automated Documentation Pipeline (implements ADR-0034)
- **SPEC-0039**: Contract-Driven Test Generation (implements ADR-0035)
- **SPEC-0040**: Observability & Tracing (implements ADR-0036)
- **SPEC-0041**: Development Environment Setup (implements ADR-0037)
- **SPEC-0042**: CI/CD Pipeline Implementation (implements ADR-0038)
- **SPEC-0043**: Deployment Infrastructure (implements ADR-0039)

### Updated SPECs

- **SPEC-0028**: Extended with data versioning (version_id, parent_version_id)
- **SPEC-0034**: Simplified API naming (removed /v1/ prefix)

## Cross-Reference Validation

All ADRs must have:

1. `implementation_specs` field pointing to SPEC documents
2. SPECs must link to `tier_0_contracts` (Pydantic models)
3. Contracts are the single source of truth for data structures

---
*Last Updated: 2025-12-28*
*Maintainer: Mycahya Eggleston*
*Total SPECs: 43 (24 core + 9 DAT + 5 PPTX + 4 SOV + 1 DevTools)*
