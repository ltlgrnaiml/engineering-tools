# Data Aggregator - Architecture Overview

> **System design for the Data Aggregator (DAT) tool**

---

## Overview

The Data Aggregator is a **profile-driven data extraction tool** that processes multiple file formats through an 8-stage guided workflow.

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                         DAT Frontend (React)                             │
│                         http://localhost:5173                            │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  Horizontal Wizard Stepper                                         │  │
│  │  [1]──[2]──[3]──[4]──[5]──[6]──[7]──[8]                          │  │
│  │  Upload Context Preview Select Agg Parse Export Complete          │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────────┐
│                         API Gateway (FastAPI)                            │
│                         http://localhost:8000/api/dat/*                  │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────────┐
│                         DAT Backend (FastAPI)                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │ Profile Engine  │  │ Adapter Factory │  │ Stage Executor  │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────────┐
│                         Storage Layer                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │ File System     │  │ Parquet Output  │  │ Profile Store   │         │
│  │ (uploads)       │  │ (parsed data)   │  │ (YAML configs)  │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Three-Layer Architecture (ADR-0011)

DAT follows a three-layer architecture for data extraction:

```text
┌─────────────────────────────────────────────────────────────────────────┐
│  PROFILE LAYER (SSoT)                                                    │
│  ─────────────────────                                                   │
│  YAML profiles define WHAT to extract                                    │
│  - 10-section schema (metadata, source, context, tables, columns, etc.) │
│  - Builtin profiles in repo, custom profiles in DB                      │
│  - Location: apps/data_aggregator/backend/src/dat_aggregation/profiles/ │
├─────────────────────────────────────────────────────────────────────────┤
│  ADAPTER LAYER (HOW)                                                     │
│  ─────────────────────                                                   │
│  File adapters execute the extraction                                    │
│  - CSVAdapter, ExcelAdapter, JSONAdapter, XMLAdapter                    │
│  - AdapterFactory selects based on file type                            │
│  - Streaming mode for files > 10MB (ADR-0040)                           │
├─────────────────────────────────────────────────────────────────────────┤
│  DATASET LAYER (OUTPUT)                                                  │
│  ─────────────────────                                                   │
│  Parquet + manifest output                                               │
│  - DataSetManifest with lineage tracking                                │
│  - Stored in workspace/datasets/{id}/                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 8-Stage Pipeline

### Stage Flow

```text
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│ Upload  │──▶│ Context │──▶│ Preview │──▶│ Select  │
│ (1)     │   │ (2)*    │   │ (3)*    │   │ (4)     │
└─────────┘   └─────────┘   └─────────┘   └─────────┘
                                               │
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌───▼─────┐
│Complete │◀──│ Export  │◀──│ Parse   │◀──│Aggregate│
│ (8)     │   │ (7)     │   │ (6)     │   │ (5)     │
└─────────┘   └─────────┘   └─────────┘   └─────────┘

* Context and Preview stages are optional (ADR-0003)
```

### Stage Descriptions

| Stage | Purpose | Key Actions |
|-------|---------|-------------|
| **1. Upload** | Ingest source file | File validation, adapter selection |
| **2. Context** | Extract metadata | JSON path extraction, regex patterns |
| **3. Preview** | Sample data preview | First N rows, schema detection |
| **4. Select** | Choose tables/columns | User selection, column mapping |
| **5. Aggregate** | Apply transformations | Grouping, pivoting, filtering |
| **6. Parse** | Execute extraction | Profile-driven parsing, Parquet output |
| **7. Export** | Save results | DataSet creation with manifest |
| **8. Complete** | Finalize workflow | Lock state, cleanup |

### Stage State Model (ADR-0001)

```text
UNLOCKED ──lock()──▶ LOCKED ──complete()──▶ COMPLETED
    ▲                   │
    └───unlock()────────┘  (cascades to downstream stages)
```

**Rules**:
- Forward gating: Cannot lock stage N until stage N-1 is locked
- Unlock cascade: Unlocking stage N unlocks all downstream stages
- Artifact preservation: Never delete artifacts on unlock (ADR-0002)

---

## Backend Architecture

### Directory Structure

```text
apps/data_aggregator/backend/
├── api/
│   ├── routes.py              # FastAPI route definitions
│   ├── errors.py              # ErrorResponse helpers
│   └── dependencies.py        # Dependency injection
├── services/
│   ├── stage_service.py       # Stage execution logic
│   ├── profile_service.py     # Profile management
│   └── adapter_service.py     # File adapter coordination
└── src/dat_aggregation/
    ├── adapters/              # File type adapters
    │   ├── base.py            # BaseFileAdapter
    │   ├── csv_adapter.py
    │   ├── excel_adapter.py
    │   ├── json_adapter.py
    │   └── xml_adapter.py
    ├── profiles/              # Profile engine
    │   ├── executor.py        # ProfileExecutor
    │   ├── loader.py          # Profile loading
    │   └── examples/          # Builtin profiles
    └── stages/                # Stage implementations
        ├── upload.py
        ├── context.py
        ├── parse.py
        └── export.py
```

### Adapter Pattern

All file adapters implement `BaseFileAdapter`:

```python
class BaseFileAdapter(ABC):
    @abstractmethod
    def probe_schema(self, path: Path) -> SchemaProbeResult:
        """Probe file schema without loading entire file."""
        ...

    @abstractmethod
    def read_data(self, path: Path, options: ReadOptions) -> pl.DataFrame:
        """Read data using Polars."""
        ...

    @abstractmethod
    def supports_streaming(self) -> bool:
        """Whether adapter supports streaming mode."""
        ...
```

### Large File Handling (ADR-0040)

| File Size | Mode | Behavior |
|-----------|------|----------|
| < 10MB | Eager | Load entire file into memory |
| ≥ 10MB | Streaming | Process in chunks |

**Performance Targets**:
- Schema probe: < 5 seconds
- Preview load: < 2 seconds (sampling)
- Memory: Must not exceed `max_memory_mb` config

---

## Frontend Architecture

### UI Pattern: Horizontal Wizard (ADR-0041)

```text
┌─────────────────────────────────────────────────────────────────────────┐
│  [●]──[○]──[○]──[○]──[○]──[○]──[○]──[○]                                │
│  Upload Context Preview Select Agg Parse Export Complete                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Stage Content Panel                                             │   │
│  │  ─────────────────────                                           │   │
│  │  - Collapsible sections                                          │   │
│  │  - Stage-specific controls                                       │   │
│  │  - Lock/Unlock buttons                                           │   │
│  │  - Progress indicators                                           │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### State Indicators

| State | Visual | Behavior |
|-------|--------|----------|
| UNLOCKED | Gray circle | Editable, can modify |
| LOCKED | Blue checkmark | Read-only, validated |
| COMPLETED | Green checkmark | Final, immutable |
| ERROR | Red X | Retry available |

---

## Data Flow

### Parse Stage Execution

```text
Profile YAML
     │
     ▼
┌────────────────┐
│ProfileExecutor │──▶ Load profile
└───────┬────────┘    Validate schema
        │
        ▼
┌────────────────┐
│AdapterFactory  │──▶ Select adapter by file type
└───────┬────────┘    Configure options
        │
        ▼
┌────────────────┐
│FileAdapter     │──▶ Read file (eager or streaming)
└───────┬────────┘    Apply extraction strategy
        │
        ▼
┌────────────────┐
│DataSetBuilder  │──▶ Build Polars DataFrame
└───────┬────────┘    Apply transformations
        │
        ▼
┌────────────────┐
│ArtifactStore   │──▶ Save as Parquet
└────────────────┘    Create manifest with lineage
```

---

## Key ADRs

| ADR | Topic |
|-----|-------|
| ADR-0001-DAT | Stage Graph Configuration |
| ADR-0003 | Optional Context/Preview Stages |
| ADR-0011 | Profile-Driven Extraction |
| ADR-0013 | Cancellation Semantics |
| ADR-0014 | Parse/Export Artifact Formats |
| ADR-0040 | Large File Streaming |
| ADR-0041 | Horizontal Wizard UI |

---

## Related Documentation

- **AGENTS.md**: `apps/data_aggregator/AGENTS.md` - AI assistant rules
- **SPECs**: `docs/specs/dat/` - Technical specifications
- **Contracts**: `shared/contracts/dat/` - Pydantic models
