# SPEC Index: Engineering Tools Platform

> **Tier 2 Documents**: SPECs define WHAT is being built (implementation details, APIs, schemas).
> They link upward to ADRs (WHY) and downward to Tier-0 Contracts (SOURCE OF TRUTH).
>
> **Context**: Solo-dev, greenfield, AI-assisted development. SPECs aligned with simplified ADRs.
>
> **Naming Convention**: SPECs use globally unique sequential numbering (BKM). Format: `SPEC-XXXX_kebab-case-title.json`. Numbers are never reused.

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
| SPEC-0002 | Concurrency Determinism | ADR-0013 | `shared/contracts/core/concurrency.py` |
| SPEC-0003 | Audit Trail Enforcement | ADR-0009 | `shared/contracts/core/audit.py` |
| SPEC-0004 | Artifact Lifecycle Preservation | ADR-0002 | `shared/contracts/core/artifact_registry.py` |
| SPEC-0005 | Deterministic Stage ID | ADR-0005 | `shared/contracts/core/id_generator.py` |
| SPEC-0006 | Path Safety And Normalization | ADR-0018#path-safety | `shared/contracts/core/path_safety.py` |
| SPEC-0007 | DataSet Lineage & Versioning | ADR-0026 | `shared/contracts/core/dataset.py` |
| SPEC-0008 | Pipeline Execution | ADR-0027 | `shared/contracts/core/pipeline.py` |
| SPEC-0009 | Unified Rendering Contracts | ADR-0029 | `shared/contracts/core/rendering.py` |
| SPEC-0010 | Rendering Engine Architecture | ADR-0029 | `shared/rendering/` |
| SPEC-0011 | Output Target Adapters | ADR-0029 | `shared/rendering/adapters/` |
| SPEC-0012 | API Naming Convention | ADR-0030 | - |
| SPEC-0013 | Error Response Implementation Guide | ADR-0032 | `shared/contracts/core/error_response.py` |
| SPEC-0014 | Idempotency Implementation Guide | ADR-0033 | `shared/contracts/core/idempotency.py` |
| SPEC-0015 | AI-Assisted Development Patterns | ADR-0034 | - (code conventions) |
| SPEC-0016 | Automated Documentation Pipeline | ADR-0035 | - (tooling) |
| SPEC-0017 | Contract-Driven Test Generation | ADR-0036 | - (testing) |
| SPEC-0018 | Observability & Tracing | ADR-0037 | `shared/contracts/core/logging.py`, `shared/contracts/core/frontend_logging.py` |
| SPEC-0019 | Development Environment Setup | ADR-0038 | - (scripts) |
| SPEC-0020 | CI/CD Pipeline Implementation | ADR-0039 | - (workflows) |
| SPEC-0021 | Deployment Infrastructure | ADR-0040 | - (Pulumi) |
| SPEC-0022 | Stage Completion Semantics | ADR-0001 | `shared/contracts/core/pipeline.py` |
| SPEC-0023 | Frontend Iframe Integration | ADR-0044 | - (frontend components) |

### DAT SPECs (Data Aggregation Tool)

| SPEC ID | Title | Implements ADR | Tier-0 Contracts |
|---------|-------|----------------|------------------|
| SPEC-0024 | DAT Stage Graph | ADR-0003 | `shared/contracts/dat/stage.py` |
| SPEC-0025 | DAT Profile Extraction | ADR-0003, ADR-0012 | `shared/contracts/dat/profile.py` |
| SPEC-0026 | DAT Adapter Interface & Registry | ADR-0012 | `shared/contracts/dat/adapter.py` |
| SPEC-0027 | DAT Large File Streaming | ADR-0041 | `shared/contracts/dat/adapter.py` |
| SPEC-0028 | DAT Profile File Management | ADR-0012, ADR-0029 | `shared/contracts/dat/profile.py` |
| SPEC-0029 | DAT Table Availability | ADR-0008 | `shared/contracts/dat/table_status.py` |
| SPEC-0030 | DAT Profile Schema | ADR-0012 | `shared/contracts/dat/profile.py` |
| SPEC-0031 | DAT Extraction Strategies | ADR-0012 | `shared/contracts/dat/profile.py` |
| SPEC-0032 | DAT Cancellation Cleanup | ADR-0014 | `shared/contracts/dat/cancellation.py` |

### DevTools SPECs

| SPEC ID | Title | Implements ADR | Tier-0 Contracts |
|---------|-------|----------------|------------------|
| SPEC-0033 | DevTools API | ADR-0028 | `shared/contracts/devtools/api.py` |
| SPEC-0034 | DevTools Workflow Manager | ADR-0045 | `shared/contracts/devtools/workflow.py` |

### PPTX SPECs (PowerPoint Generator)

| SPEC ID | Title | Implements ADR | Tier-0 Contracts |
|---------|-------|----------------|------------------|
| SPEC-0035 | PPTX Template Schema | ADR-0019 | `shared/contracts/pptx/template.py` |
| SPEC-0036 | PPTX Shape Discovery | ADR-0019 | `shared/contracts/pptx/shape.py` |
| SPEC-0037 | PPTX Renderer Interface | ADR-0022 | `shared/contracts/pptx/renderer.py` |

### SOV SPECs (Source of Variance Analyzer)

| SPEC ID | Title | Implements ADR | Tier-0 Contracts |
|---------|-------|----------------|------------------|
| SPEC-0038 | SOV ANOVA Computation | ADR-0023 | `shared/contracts/sov/anova.py` |
| SPEC-0039 | SOV Visualization Contracts | ADR-0025 | `shared/contracts/sov/visualization.py` |

### Workflow SPECs

| SPEC ID | Title | Implements ADR | Tier-0 Contracts |
|---------|-------|----------------|------------------|
| SPEC-0040 | AI Development Workflow Execution | ADR-0043 | `shared/contracts/plan_schema.py` |

## Tier-0 Contract Status

### Core Contracts 

| Contract | Location | Key Classes | Used By |
|----------|----------|-------------|---------|
| ADRSchema | `shared/contracts/adr_schema.py` | ADRSchema, Provenance | SPEC-0009 |
| Pipeline | `shared/contracts/core/pipeline.py` | Pipeline, PipelineStep, PipelineStepState | SPEC-0001, SPEC-0008 |
| DataSet | `shared/contracts/core/dataset.py` | DataSetManifest, ColumnMeta, DataSetRef | SPEC-0007 |
| ArtifactRegistry | `shared/contracts/core/artifact_registry.py` | ArtifactRecord, ArtifactQuery | SPEC-0004 |
| Audit | `shared/contracts/core/audit.py` | AuditTimestamp, AuditTrail, LifecycleEvent, TimestampMixin | SPEC-0003 |
| PathSafety | `shared/contracts/core/path_safety.py` | RelativePath, WorkspacePath, PathValidationError | SPEC-0006 |
| Concurrency | `shared/contracts/core/concurrency.py` | PlatformInfo, ConcurrencyConfig, OSType, ShellType | SPEC-0002, SPEC-0019 |
| **Rendering** | `shared/contracts/core/rendering.py` | RenderSpec, ChartSpec, TableSpec, RenderStyle, DataSeries, OutputTarget | SPEC-0009, SPEC-0010, SPEC-0002 |
| **IDGenerator** | `shared/contracts/core/id_generator.py` | IDConfig, compute_deterministic_id, StageIDInputs, UploadStageInputs, ParseStageInputs | SPEC-0005 |
| **Logging** | `shared/contracts/core/logging.py` | LogEvent, RequestContext, StateSnapshot, FSMTransitionLog, ArtifactLog, TraceQuery, TraceResult | SPEC-0018 |
| **FrontendLogging** | `shared/contracts/core/frontend_logging.py` | FrontendLogEntry, FrontendAPICall, FrontendStateTransition, FrontendDebugExport, DebugPanelConfig | SPEC-0018 |

### DAT Contracts ✓

| Contract | Location | Key Classes | Used By |
|----------|----------|-------------|---------|
| **Stage** | `shared/contracts/dat/stage.py` | DATStageState, DATStageConfig, DATStageResult, ParseStageConfig, AggregateStageConfig, ExportStageConfig | SPEC-0024 |
| **Profile** | `shared/contracts/dat/profile.py` | ExtractionProfile, ColumnMapping, AggregationRule, FilePattern, ValidationRule | SPEC-0025, SPEC-0007 |
| **Adapter** | `shared/contracts/dat/adapter.py` (NEW) | BaseFileAdapter, AdapterMetadata, AdapterCapabilities, SchemaProbeResult, ReadOptions, StreamOptions | SPEC-0026, SPEC-0027 |
| **TableStatus** | `shared/contracts/dat/table_status.py` | TableAvailability, TableAvailabilityStatus, TableStatusReport, TableHealth | SPEC-0008 |
| **Cancellation** | `shared/contracts/dat/cancellation.py` | CancellationRequest, CancellationResult, Checkpoint, CheckpointRegistry, CleanupRequest, CancellationAuditLog | SPEC-0010 |

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
| **Catalog** | `shared/contracts/messages/catalog.py` | MessageDefinition, MessageCatalog, ErrorMessage, ProgressMessage, ValidationMessage | SPEC-0005, ADR-0018#message-catalogs |

### DevTools Contracts ✓

| Contract | Location | Key Classes | Used By |
|----------|----------|-------------|---------|
| **API** | `shared/contracts/devtools/api.py` | DevToolsState, ADRListResponse, ADRSaveRequest, SchemaValidationRequest, APITestRequest | SPEC-0033 |

### Rendering Engine Implementation ✓

| Module | Location | Key Classes | Used By |
|--------|----------|-------------|---------|
| **Engine** | `shared/rendering/engine.py` | RenderEngine | SPEC-0010 |
| **Registry** | `shared/rendering/registry.py` | AdapterRegistry, get_adapter, register_adapter | SPEC-0002 |
| **BaseAdapter** | `shared/rendering/adapters/base.py` | BaseOutputAdapter, MatplotlibAdapterMixin | SPEC-0002 |
| **JSONAdapter** | `shared/rendering/adapters/json_adapter.py` | JSONAdapter | SPEC-0002 |

## SPEC Numbering Refactor (2025-12-30)

All SPECs were renumbered to follow industry BKM:
- Global sequential numbering (no duplicates across domains)
- Contiguous numbering (no gaps)
- Lowercase kebab-case titles
- Format: `SPEC-XXXX_title.json`

### Mapping Reference

| Old ID | New ID |
|--------|--------|
| SPEC-0011 | SPEC-0002 |
| SPEC-0012 | SPEC-0003 |
| SPEC-0013 | SPEC-0004 |
| SPEC-0014 | SPEC-0005 |
| SPEC-0016 | SPEC-0006 |
| SPEC-0028 | SPEC-0007 |
| SPEC-0029 | SPEC-0008 |
| SPEC-0031 | SPEC-0009 |
| SPEC-0032 | SPEC-0010 |
| SPEC-0033 | SPEC-0011 |
| SPEC-0034 | SPEC-0012 |
| SPEC-0035 | SPEC-0013 |
| SPEC-0036 | SPEC-0014 |
| SPEC-0037 | SPEC-0015 |
| SPEC-0038 | SPEC-0016 |
| SPEC-0039 | SPEC-0017 |
| SPEC-0040 | SPEC-0018 |
| SPEC-0041 | SPEC-0019 |
| SPEC-0042 | SPEC-0020 |
| SPEC-0043 | SPEC-0021 |
| SPEC-0044 | SPEC-0022 |
| SPEC-0045 | SPEC-0023 |
| SPEC-DAT-0001 | SPEC-0024 |
| SPEC-DAT-0002 | SPEC-0025 |
| SPEC-DAT-0003 | SPEC-0026 |
| SPEC-DAT-0004 | SPEC-0027 |
| SPEC-DAT-0005 | SPEC-0028 |
| SPEC-DAT-0006 | SPEC-0029 |
| SPEC-DAT-0011 | SPEC-0030 |
| SPEC-DAT-0012 | SPEC-0031 |
| SPEC-DAT-0015 | SPEC-0032 |
| SPEC-0030 (devtools) | SPEC-0033 |
| SPEC-0046 | SPEC-0034 |
| SPEC-PPTX-0019 | SPEC-0035 |
| SPEC-PPTX-0020 | SPEC-0036 |
| SPEC-PPTX-0023 | SPEC-0037 |
| SPEC-SOV-0024 | SPEC-0038 |
| SPEC-SOV-0027 | SPEC-0039 |

## Cross-Reference Validation

All ADRs must have:

1. `implementation_specs` field pointing to SPEC documents
2. SPECs must link to `tier_0_contracts` (Pydantic models)
3. Contracts are the single source of truth for data structures

---
*Last Updated: 2025-12-30*
*Maintainer: Mycahya Eggleston*
*Total SPECs: 39 (23 core + 9 DAT + 3 PPTX + 2 SOV + 2 DevTools)*
