# Tier 2: File-Level Change Specifications

**Purpose**: Exact files to create, modify, or delete for each milestone.

---

## Milestone 1: Unify Adapter Implementations

### Files to DELETE

```
apps/data_aggregator/backend/src/dat_aggregation/adapters/
├── __init__.py           # DELETE
├── base.py               # DELETE
├── csv_adapter.py        # DELETE
├── excel_adapter.py      # DELETE
├── json_adapter.py       # DELETE
├── parquet_adapter.py    # DELETE
└── factory.py            # DELETE
```

### Files to MODIFY

#### M1-MOD-001: `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py`

**Change**: Update adapter imports

| Line | Old Import | New Import |
|------|------------|------------|
| ~616 | `from ..adapters.factory import AdapterFactory` | `from apps.data_aggregator.backend.adapters.registry import AdapterRegistry` |
| ~669 | `from ..adapters.factory import AdapterFactory` | (same) |
| ~808 | `from ..adapters.factory import AdapterFactory` | (same) |

**Change**: Update usage

| Old | New |
|-----|-----|
| `AdapterFactory.get_adapter(path)` | `AdapterRegistry.get_adapter(path)` |
| `AdapterFactory.get_tables(path)` | `AdapterRegistry.get_adapter(path).get_tables()` |
| `AdapterFactory.get_preview(path, ...)` | `AdapterRegistry.get_adapter(path).read(path, ...)` |

#### M1-MOD-002: `apps/data_aggregator/backend/src/dat_aggregation/stages/parse.py`

**Change**: Update adapter import if present

#### M1-MOD-003: `apps/data_aggregator/backend/src/dat_aggregation/stages/table_availability.py`

**Change**: Update adapter import if present

---

## Milestone 2: API Path Normalization

### Files to MODIFY

#### M2-MOD-001: `gateway/main.py`

**Lines ~43-45**: Remove `/v1/` from router prefixes

```python
# BEFORE
app.include_router(dataset_router, prefix="/api/v1/datasets", tags=["datasets"])
app.include_router(pipeline_router, prefix="/api/v1/pipelines", tags=["pipelines"])
app.include_router(devtools_router, prefix="/api/v1/devtools", tags=["devtools"])

# AFTER
app.include_router(dataset_router, prefix="/api/datasets", tags=["datasets"])
app.include_router(pipeline_router, prefix="/api/pipelines", tags=["pipelines"])
app.include_router(devtools_router, prefix="/api/devtools", tags=["devtools"])
```

#### M2-MOD-002: `gateway/services/pipeline_service.py`

**Lines ~32-36**: Update tool base URLs

```python
# BEFORE
TOOL_BASE_URLS = {
    "dat": "http://localhost:8000/api/dat/v1",
    "sov": "http://localhost:8000/api/sov/v1",
    "pptx": "http://localhost:8000/api/pptx/v1",
}

# AFTER
TOOL_BASE_URLS = {
    "dat": "http://localhost:8000/api/dat",
    "sov": "http://localhost:8000/api/sov",
    "pptx": "http://localhost:8000/api/pptx",
}
```

#### M2-MOD-003: `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py`

**Line 39**: Remove `/v1` prefix

```python
# BEFORE
router = APIRouter(prefix="/v1")

# AFTER
router = APIRouter()
```

**Line 3**: Update docstring

```python
# BEFORE
"""DAT API routes.

Per ADR-0030: All routes use versioned /v1/ prefix.

# AFTER
"""DAT API routes.

Per ADR-0030: All routes use /api/{tool}/{resource} pattern (no version prefix).
```

#### M2-MOD-004: `apps/sov_analyzer/backend/src/sov_analyzer/api/routes.py`

**Change**: Remove `/v1` prefix from router

#### M2-MOD-005: `apps/pptx_generator/backend/main.py`

**Change**: Remove `/v1/` from all router prefixes

### Frontend Files to MODIFY

#### M2-MOD-006: `apps/data_aggregator/frontend/src/hooks/useRun.ts`

**Change**: Replace all `/api/dat/v1/` with `/api/dat/`

#### M2-MOD-007: `apps/data_aggregator/frontend/src/components/stages/*.tsx`

**Files**:
- `SelectionPanel.tsx`
- `ParsePanel.tsx`
- `PreviewPanel.tsx`
- `ContextPanel.tsx`
- `ExportPanel.tsx`
- `TableAvailabilityPanel.tsx`
- `TableSelectionPanel.tsx`

**Change**: Replace all `/api/dat/v1/` with `/api/dat/`

#### M2-MOD-008: `apps/sov_analyzer/frontend/src/components/AnalysisConfig.tsx`

**Change**: Replace all `/api/sov/v1/` with `/api/sov/`

#### M2-MOD-009: Homepage Frontend Files

**Files**:
- `apps/homepage/frontend/src/hooks/usePipelines.ts`
- `apps/homepage/frontend/src/hooks/useDataSets.ts`
- `apps/homepage/frontend/src/pages/DataSetDetailsPage.tsx`
- `apps/homepage/frontend/src/pages/PipelineDetailsPage.tsx`
- `apps/homepage/frontend/src/pages/PipelinesPage.tsx`
- `apps/homepage/frontend/src/pages/DevToolsPage.tsx`

**Change**: Replace all `/api/*/v1/` with `/api/*/`

### Test Files to MODIFY

#### M2-MOD-010: Test Files

**Files** (update API paths):
- `tests/dat/test_api.py` (~26 occurrences)
- `tests/test_gateway.py` (~13 occurrences)
- `tests/test_all_endpoints.py` (~10 occurrences)
- `tests/integration/test_gateway_api.py` (~5 occurrences)
- `tests/unit/test_devtools_api.py` (~2 occurrences)
- `test_endpoints_standalone.py` (~8 occurrences)

---

## Milestone 3: Externalize Stage Graph Configuration

### Files to CREATE

#### M3-NEW-001: `shared/contracts/dat/stage_graph.py`

**Purpose**: Tier-0 contract for stage graph configuration

**Contents**: See `03_IMPLEMENTATION_DETAILS.md` for full code

### Files to MODIFY

#### M3-MOD-001: `shared/contracts/dat/__init__.py`

**Change**: Add exports for new contract

```python
from shared.contracts.dat.stage_graph import (
    StageGraphConfig,
    StageDefinition,
    GatingRule,
    CascadeRule,
)
```

**Change**: Update `__all__` list

#### M3-MOD-002: `apps/data_aggregator/backend/src/dat_aggregation/core/state_machine.py`

**Change**: Remove module-level dicts, add config injection

**Lines to DELETE (~41-71)**:
```python
FORWARD_GATES: dict[Stage, list[tuple[Stage, bool]]] = { ... }
CASCADE_TARGETS: dict[Stage, list[Stage]] = { ... }
```

**Change**: Update `__init__` signature and add lookup builders

### Files to DELETE

#### M3-DEL-001: `apps/data_aggregator/backend/src/dat_aggregation/core/stage_graph_config.py`

**Status**: Delete if exists (orphaned file)

---

## Milestone 4: Align Stage ID Generation

### Files to MODIFY

#### M4-MOD-001: `shared/utils/stage_id.py`

**Line ~44**: Change hash length from 16 to 8

```python
# BEFORE
hash_digest = hashlib.sha256(serialized.encode()).hexdigest()[:16]

# AFTER
hash_digest = hashlib.sha256(serialized.encode()).hexdigest()[:8]
```

#### M4-MOD-002: `apps/data_aggregator/backend/src/dat_aggregation/core/state_machine.py`

**Change**: Update `_get_stage_inputs` to use relative paths

#### M4-MOD-003: `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py`

**Line ~234**: Use relative paths in discovery inputs

```python
# BEFORE
inputs = {"root_path": str(source_path)}

# AFTER
from shared.contracts.core.path_safety import to_relative_path
inputs = {"root_path": to_relative_path(source_path, workspace_root)}
```

### Files to VERIFY/CREATE

#### M4-VER-001: `shared/contracts/core/path_safety.py`

**Verify** `to_relative_path()` function exists. If not, create it.

---

## Milestone 5: Table Availability Fast Probe

### Files to CREATE

#### M5-NEW-001: `apps/data_aggregator/backend/services/table_probe.py`

**Purpose**: Fast table probing service with timeout

**Contents**: See `03_IMPLEMENTATION_DETAILS.md`

### Files to MODIFY

#### M5-MOD-001: `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py`

**Lines ~596-706**: Replace `adapter.read()` with `probe_table()`

---

## Milestone 6: Large File Streaming

### Files to MODIFY

#### M6-MOD-001: `apps/data_aggregator/backend/src/dat_aggregation/stages/parse.py`

**Change**: Add streaming threshold and conditional logic

```python
STREAMING_THRESHOLD_BYTES = 10 * 1024 * 1024  # 10MB
```

#### M6-MOD-002: Verify All Adapters

**Files to verify** (must have `stream_dataframe()` method):
- `apps/data_aggregator/backend/adapters/csv_adapter.py`
- `apps/data_aggregator/backend/adapters/excel_adapter.py`
- `apps/data_aggregator/backend/adapters/json_adapter.py`
- `apps/data_aggregator/backend/adapters/parquet_adapter.py`

---

## Milestone 7: Parse/Export Artifact Formats

### Files to MODIFY

#### M7-MOD-001: `apps/data_aggregator/backend/src/dat_aggregation/stages/parse.py`

**Change**: Enforce Parquet output

```python
OUTPUT_FORMAT = "parquet"  # Enforced per ADR-0015
```

#### M7-MOD-002: `apps/data_aggregator/backend/src/dat_aggregation/stages/export.py`

**Change**: Add multi-format support

```python
SUPPORTED_FORMATS = {"parquet", "csv", "excel", "json"}
```

---

## Milestone 8: Cancellation Checkpointing

### Files to CREATE

#### M8-NEW-001: `apps/data_aggregator/backend/services/checkpoint.py`

**Purpose**: Checkpoint registry for cancellation safety

#### M8-NEW-002: `apps/data_aggregator/backend/services/cleanup.py`

**Purpose**: Explicit cleanup service (dry-run by default)

### Files to MODIFY

#### M8-MOD-001: `apps/data_aggregator/backend/src/dat_aggregation/stages/parse.py`

**Change**: Add checkpoint calls after table completion

#### M8-MOD-002: `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py`

**Change**: Add cleanup endpoint

```python
@router.post("/runs/{run_id}/cleanup")
async def cleanup_run(run_id: str, request: CleanupRequest):
    ...
```

---

## Milestone 9: Profile CRUD

### Files to CREATE

#### M9-NEW-001: `apps/data_aggregator/backend/services/profile_service.py`

**Purpose**: Profile CRUD service with deterministic IDs

### Files to MODIFY

#### M9-MOD-001: `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py`

**Change**: Add CRUD endpoints

```python
@router.post("/profiles", response_model=ExtractionProfile)
@router.get("/profiles/{profile_id}", response_model=ExtractionProfile)
@router.put("/profiles/{profile_id}", response_model=ExtractionProfile)
@router.delete("/profiles/{profile_id}")
```

---

## Summary Table

| Milestone | New Files | Modified Files | Deleted Files |
|-----------|-----------|----------------|---------------|
| M1 | 0 | 3 | 7 |
| M2 | 0 | 20+ | 0 |
| M3 | 1 | 2 | 1 |
| M4 | 0-1 | 3 | 0 |
| M5 | 1 | 1 | 0 |
| M6 | 0 | 5 | 0 |
| M7 | 0 | 2 | 0 |
| M8 | 2 | 2 | 0 |
| M9 | 1 | 1 | 0 |

---

*Next: Read `03_IMPLEMENTATION_DETAILS.md`*
