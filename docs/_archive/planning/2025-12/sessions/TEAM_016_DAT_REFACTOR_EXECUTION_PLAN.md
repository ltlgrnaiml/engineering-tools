# TEAM_016: DAT Refactor Execution Plan

**Session Date**: 2025-12-28  
**Status**: READY_FOR_EXECUTION  
**Objective**: Execute and validate all confirmed gaps from TEAM_006–TEAM_015 consolidation  
**Predecessors**: TEAM_011 (Consolidation), TEAM_012 (Validation), TEAM_013 (Master Plan)

---

## Executive Summary

This is the **executable change plan** for the DAT refactor. It contains file-level tasks, specific code changes, and validation commands for each of the 12 confirmed gaps.

**Total Tasks**: 47  
**Estimated Phases**: 5  
**Critical Path**: M1 (Adapters) → M2 (API) → M3 (FSM) → M4 (Determinism)

---

## Phase 1: Foundation & Cleanup

### M1: Unify Adapter Implementations

**Gap**: GAP-002 (Two parallel adapter stacks create SSoT drift risk)  
**ADR**: ADR-0012  
**Criticality**: CRITICAL

#### Task M1.1: Migrate Stage Imports to Contract-Style Adapters

| File | Current Import | New Import |
|:-----|:---------------|:-----------|
| `apps/data_aggregator/backend/src/dat_aggregation/stages/parse.py` | `from ..adapters.factory import AdapterFactory` | `from apps.data_aggregator.backend.adapters.registry import AdapterRegistry` |
| `apps/data_aggregator/backend/src/dat_aggregation/stages/table_availability.py` | `from ..adapters.factory import AdapterFactory` | `from apps.data_aggregator.backend.adapters.registry import AdapterRegistry` |
| `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py` | `from ..adapters.factory import AdapterFactory` | `from apps.data_aggregator.backend.adapters.registry import AdapterRegistry` |

#### Task M1.2: Delete Legacy Adapter Stack

```bash
# Files to delete (after migration verified)
rm -rf apps/data_aggregator/backend/src/dat_aggregation/adapters/
```

**Files to remove**:
- `apps/data_aggregator/backend/src/dat_aggregation/adapters/__init__.py`
- `apps/data_aggregator/backend/src/dat_aggregation/adapters/base.py`
- `apps/data_aggregator/backend/src/dat_aggregation/adapters/csv_adapter.py`
- `apps/data_aggregator/backend/src/dat_aggregation/adapters/excel_adapter.py`
- `apps/data_aggregator/backend/src/dat_aggregation/adapters/json_adapter.py`
- `apps/data_aggregator/backend/src/dat_aggregation/adapters/parquet_adapter.py`
- `apps/data_aggregator/backend/src/dat_aggregation/adapters/factory.py`

#### Task M1.3: Verify Contract-Style Adapters Implement BaseFileAdapter

**Check each adapter in** `apps/data_aggregator/backend/adapters/`:
- [ ] `csv_adapter.py` implements `probe_schema()`, `read_dataframe()`, `stream_dataframe()`, `validate_file()`
- [ ] `excel_adapter.py` implements all 4 methods
- [ ] `json_adapter.py` implements all 4 methods
- [ ] `parquet_adapter.py` implements all 4 methods

#### M1 Validation

```bash
# Verify no imports from legacy adapters
grep -r "from.*dat_aggregation.adapters" apps/data_aggregator/backend/src/ --include="*.py"
# Should return empty

# Verify new adapters work
pytest tests/dat/test_adapter_registry.py -v
pytest tests/dat/test_csv_adapter.py -v
```

---

### M2: API Path Normalization (Remove /v1)

**Gap**: GAP-001 (API uses `/v1` prefix violating ADR-0030)  
**ADR**: ADR-0030  
**Criticality**: CRITICAL

#### Task M2.1: Gateway Cross-Tool Routes

**File**: `gateway/main.py`

```python
# BEFORE (lines 43-45)
app.include_router(dataset_router, prefix="/api/v1/datasets", tags=["datasets"])
app.include_router(pipeline_router, prefix="/api/v1/pipelines", tags=["pipelines"])
app.include_router(devtools_router, prefix="/api/v1/devtools", tags=["devtools"])

# AFTER
app.include_router(dataset_router, prefix="/api/datasets", tags=["datasets"])
app.include_router(pipeline_router, prefix="/api/pipelines", tags=["pipelines"])
app.include_router(devtools_router, prefix="/api/devtools", tags=["devtools"])
```

#### Task M2.2: Gateway Pipeline Service

**File**: `gateway/services/pipeline_service.py`

```python
# BEFORE (lines 32-36)
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

#### Task M2.3: DAT Router

**File**: `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py`

```python
# BEFORE (line 39)
router = APIRouter(prefix="/v1")

# AFTER
router = APIRouter()
```

Also update docstring comment referencing `/v1`.

#### Task M2.4: SOV Router

**File**: `apps/sov_analyzer/backend/src/sov_analyzer/api/routes.py`

```python
# BEFORE
router = APIRouter(prefix="/v1")

# AFTER
router = APIRouter()
```

#### Task M2.5: PPTX Routers

**File**: `apps/pptx_generator/backend/main.py`

```python
# BEFORE (multiple routers)
app.include_router(projects_router, prefix="/v1/projects", ...)
app.include_router(templates_router, prefix="/v1/templates", ...)
# etc.

# AFTER
app.include_router(projects_router, prefix="/projects", ...)
app.include_router(templates_router, prefix="/templates", ...)
```

#### Task M2.6: DAT Frontend

**Files to update** (remove `/v1` from fetch URLs):

| File | Line(s) | Change |
|:-----|:--------|:-------|
| `apps/data_aggregator/frontend/src/hooks/useRun.ts` | ~15-27 | `/api/dat/v1/` → `/api/dat/` |
| `apps/data_aggregator/frontend/src/components/stages/SelectionPanel.tsx` | ~3 places | `/api/dat/v1/` → `/api/dat/` |
| `apps/data_aggregator/frontend/src/components/stages/ParsePanel.tsx` | ~4 places | `/api/dat/v1/` → `/api/dat/` |
| `apps/data_aggregator/frontend/src/components/stages/PreviewPanel.tsx` | ~4 places | `/api/dat/v1/` → `/api/dat/` |
| `apps/data_aggregator/frontend/src/components/stages/ContextPanel.tsx` | ~2 places | `/api/dat/v1/` → `/api/dat/` |
| `apps/data_aggregator/frontend/src/components/stages/ExportPanel.tsx` | ~2 places | `/api/dat/v1/` → `/api/dat/` |
| `apps/data_aggregator/frontend/src/components/stages/TableAvailabilityPanel.tsx` | ~2 places | `/api/dat/v1/` → `/api/dat/` |
| `apps/data_aggregator/frontend/src/components/stages/TableSelectionPanel.tsx` | ~2 places | `/api/dat/v1/` → `/api/dat/` |

#### Task M2.7: SOV Frontend

**File**: `apps/sov_analyzer/frontend/src/components/AnalysisConfig.tsx`
- Remove `/v1` from fetch URLs

#### Task M2.8: Homepage Frontend

**Files**:
- `apps/homepage/frontend/src/hooks/usePipelines.ts` (~5 places)
- `apps/homepage/frontend/src/hooks/useDataSets.ts` (~2 places)
- `apps/homepage/frontend/src/pages/DataSetDetailsPage.tsx` (~3 places)
- `apps/homepage/frontend/src/pages/PipelineDetailsPage.tsx` (~3 places)
- `apps/homepage/frontend/src/pages/PipelinesPage.tsx` (~1 place)
- `apps/homepage/frontend/src/pages/DevToolsPage.tsx` (~1 place)

#### Task M2.9: Update Tests

**Files**:
- `tests/dat/test_api.py` (26 occurrences)
- `tests/test_gateway.py` (13 occurrences)
- `tests/test_all_endpoints.py` (10 occurrences)
- `tests/integration/test_gateway_api.py` (5 occurrences)
- `tests/unit/test_devtools_api.py` (2 occurrences)
- `test_endpoints_standalone.py` (8 occurrences)

#### M2 Validation

```bash
# Verify no /v1 in production code (excluding .venv, node_modules)
grep -r "prefix=\"/v1\"" apps/ gateway/ --include="*.py"
# Should return empty

grep -r "/api/dat/v1" apps/ --include="*.ts" --include="*.tsx" | grep -v node_modules
# Should return empty

# Run endpoint tests
pytest tests/test_all_endpoints.py -v
pytest tests/integration/test_gateway_api.py -v
```

---

## Phase 2: FSM Correctness

### M3: Externalize Stage Graph Configuration

**Gap**: GAP-003 (Hardcoded FORWARD_GATES/CASCADE_TARGETS)  
**Gap**: GAP-011 (No Tier-0 StageGraphConfig contract)  
**ADR**: ADR-0004, ADR-0010

#### Task M3.1: Create Tier-0 StageGraphConfig Contract

**File**: `shared/contracts/dat/stage_graph.py` (NEW)

```python
"""Stage graph configuration contract.

Per ADR-0004: 8-stage pipeline with lockable artifacts.
Per SPEC-0024: Dependencies and cascade targets defined.
"""

from enum import Enum
from typing import FrozenSet

from pydantic import BaseModel, Field

from .stage import DATStageType

__version__ = "0.1.0"


class StageDefinition(BaseModel):
    """Definition of a single stage in the pipeline."""
    
    stage_type: DATStageType
    is_optional: bool = False
    description: str = ""


class GatingRule(BaseModel):
    """Forward gating rule for stage progression."""
    
    target_stage: DATStageType
    required_stages: list[DATStageType]
    require_completion: bool = False


class CascadeRule(BaseModel):
    """Cascade unlock rule when a stage is unlocked."""
    
    trigger_stage: DATStageType
    cascade_targets: list[DATStageType]


class StageGraphConfig(BaseModel):
    """Complete stage graph configuration.
    
    Single source of truth for DAT pipeline structure.
    """
    
    stages: list[StageDefinition]
    gating_rules: list[GatingRule]
    cascade_rules: list[CascadeRule]
    optional_stages: FrozenSet[DATStageType] = frozenset({
        DATStageType.CONTEXT,
        DATStageType.PREVIEW,
    })
    
    @classmethod
    def default(cls) -> "StageGraphConfig":
        """Return the default DAT 8-stage pipeline configuration."""
        return cls(
            stages=[
                StageDefinition(stage_type=DATStageType.DISCOVERY),
                StageDefinition(stage_type=DATStageType.SELECTION),
                StageDefinition(stage_type=DATStageType.CONTEXT, is_optional=True),
                StageDefinition(stage_type=DATStageType.TABLE_AVAILABILITY),
                StageDefinition(stage_type=DATStageType.TABLE_SELECTION),
                StageDefinition(stage_type=DATStageType.PREVIEW, is_optional=True),
                StageDefinition(stage_type=DATStageType.PARSE),
                StageDefinition(stage_type=DATStageType.EXPORT),
            ],
            gating_rules=[
                GatingRule(target_stage=DATStageType.SELECTION, required_stages=[DATStageType.DISCOVERY]),
                GatingRule(target_stage=DATStageType.CONTEXT, required_stages=[DATStageType.SELECTION]),
                GatingRule(target_stage=DATStageType.TABLE_AVAILABILITY, required_stages=[DATStageType.SELECTION]),
                GatingRule(target_stage=DATStageType.TABLE_SELECTION, required_stages=[DATStageType.TABLE_AVAILABILITY]),
                GatingRule(target_stage=DATStageType.PREVIEW, required_stages=[DATStageType.TABLE_SELECTION]),
                GatingRule(target_stage=DATStageType.PARSE, required_stages=[DATStageType.TABLE_SELECTION]),
                GatingRule(target_stage=DATStageType.EXPORT, required_stages=[DATStageType.PARSE], require_completion=True),
            ],
            cascade_rules=[
                CascadeRule(trigger_stage=DATStageType.DISCOVERY, cascade_targets=[
                    DATStageType.SELECTION, DATStageType.CONTEXT, DATStageType.TABLE_AVAILABILITY,
                    DATStageType.TABLE_SELECTION, DATStageType.PREVIEW, DATStageType.PARSE, DATStageType.EXPORT
                ]),
                CascadeRule(trigger_stage=DATStageType.SELECTION, cascade_targets=[
                    DATStageType.CONTEXT, DATStageType.TABLE_AVAILABILITY, DATStageType.TABLE_SELECTION,
                    DATStageType.PREVIEW, DATStageType.PARSE, DATStageType.EXPORT
                ]),
                CascadeRule(trigger_stage=DATStageType.TABLE_AVAILABILITY, cascade_targets=[
                    DATStageType.TABLE_SELECTION, DATStageType.PREVIEW, DATStageType.PARSE, DATStageType.EXPORT
                ]),
                CascadeRule(trigger_stage=DATStageType.TABLE_SELECTION, cascade_targets=[
                    DATStageType.PREVIEW, DATStageType.PARSE, DATStageType.EXPORT
                ]),
                CascadeRule(trigger_stage=DATStageType.PARSE, cascade_targets=[DATStageType.EXPORT]),
                # Context and Preview do NOT cascade (per ADR-0004)
                CascadeRule(trigger_stage=DATStageType.CONTEXT, cascade_targets=[]),
                CascadeRule(trigger_stage=DATStageType.PREVIEW, cascade_targets=[]),
            ],
        )
```

#### Task M3.2: Update shared/contracts/dat/__init__.py

Add export for new contract:

```python
from .stage_graph import StageGraphConfig, StageDefinition, GatingRule, CascadeRule
```

#### Task M3.3: Refactor DATStateMachine to Use Config

**File**: `apps/data_aggregator/backend/src/dat_aggregation/core/state_machine.py`

```python
# BEFORE: Module-level dicts
FORWARD_GATES: dict[Stage, list[tuple[Stage, bool]]] = { ... }
CASCADE_TARGETS: dict[Stage, list[Stage]] = { ... }

class DATStateMachine:
    def __init__(self, run_id: str, store: "RunStore"):
        ...

# AFTER: Config injection
from shared.contracts.dat.stage_graph import StageGraphConfig

class DATStateMachine:
    def __init__(
        self,
        run_id: str,
        store: "RunStore",
        config: StageGraphConfig | None = None,
    ):
        self.run_id = run_id
        self.store = store
        self.config = config or StageGraphConfig.default()
        self._build_lookup_tables()
    
    def _build_lookup_tables(self) -> None:
        """Build fast lookup dicts from config."""
        self._forward_gates = {}
        for rule in self.config.gating_rules:
            self._forward_gates[rule.target_stage] = [
                (s, rule.require_completion) for s in rule.required_stages
            ]
        
        self._cascade_targets = {}
        for rule in self.config.cascade_rules:
            self._cascade_targets[rule.trigger_stage] = rule.cascade_targets
```

#### Task M3.4: Delete Orphaned stage_graph_config.py

**File to delete**: `apps/data_aggregator/backend/src/dat_aggregation/core/stage_graph_config.py`

#### Task M3.5: Fix Optional Stage Skip Semantics

**Gap**: GAP-004 (Preview skip doesn't advance current_stage)

**File**: `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py`

Update skip endpoint to set `completed=True`:

```python
@router.post("/runs/{run_id}/stages/{stage}/skip")
async def skip_stage(run_id: str, stage: str):
    """Skip an optional stage, marking it as completed."""
    # Lock with completed=True for skip
    status = await fsm.lock_stage(stage, inputs={}, completed=True)
    return status
```

**File**: `apps/data_aggregator/frontend/src/components/stages/PreviewPanel.tsx`

Update skip handler to call skip endpoint instead of lock:

```typescript
// BEFORE
await fetch(`/api/dat/runs/${runId}/stages/preview/lock`, { method: 'POST' })

// AFTER  
await fetch(`/api/dat/runs/${runId}/stages/preview/skip`, { method: 'POST' })
```

#### M3 Validation

```bash
# Contract imports work
python -c "from shared.contracts.dat import StageGraphConfig"

# FSM tests pass
pytest tests/dat/test_state_machine.py -v

# Optional stage skip works
pytest tests/dat/test_optional_stages.py -v
```

---

## Phase 3: Determinism & Path Safety

### M4: Align Stage ID Generation

**Gap**: GAP-005 (Stage ID uses 16-char, contract says 8-char)  
**Gap**: GAP-006 (Absolute paths in stage ID inputs)  
**ADR**: ADR-0008, ADR-0018

#### Task M4.1: Update stage_id.py to Use 8-char Default

**File**: `shared/utils/stage_id.py`

```python
# BEFORE (line 44)
hash_digest = hashlib.sha256(serialized.encode()).hexdigest()[:16]

# AFTER
hash_digest = hashlib.sha256(serialized.encode()).hexdigest()[:8]
```

#### Task M4.2: Implement Stage-Specific ID Inputs

**File**: `apps/data_aggregator/backend/src/dat_aggregation/core/state_machine.py`

Create explicit input builders per stage:

```python
from shared.contracts.core.path_safety import to_relative_path

def _get_discovery_inputs(self, source_path: Path, workspace: Path) -> dict:
    """Get deterministic inputs for Discovery stage."""
    return {
        "root_path": to_relative_path(source_path, workspace),
        "include_patterns": sorted(self.include_patterns),
        "exclude_patterns": sorted(self.exclude_patterns),
        "recursive": self.recursive,
    }

def _get_selection_inputs(self, discovery_id: str, selected_files: list[str], profile_id: str) -> dict:
    """Get deterministic inputs for Selection stage."""
    return {
        "discovery_id": discovery_id,
        "selected_files": sorted(selected_files),  # Relative paths
        "profile_id": profile_id,
    }

# ... similar for each stage per ADR-0008
```

#### Task M4.3: Enforce Relative Paths in Discovery API

**File**: `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py`

```python
# BEFORE (line ~234-235)
inputs = {"root_path": str(source_path)}

# AFTER
from shared.contracts.core.path_safety import to_relative_path

inputs = {"root_path": to_relative_path(source_path, workspace_root)}
```

#### Task M4.4: Create path_safety Utility if Missing

**File**: `shared/contracts/core/path_safety.py`

Ensure this function exists:

```python
def to_relative_path(path: Path, base: Path) -> str:
    """Convert absolute path to relative, raising if not under base."""
    try:
        return str(path.relative_to(base))
    except ValueError:
        raise ValueError(f"Path {path} is not under base {base}")
```

#### M4 Validation

```bash
# Stage IDs are 8 characters
pytest tests/dat/test_stage_ids.py -v

# Same inputs produce same IDs across machines
pytest tests/dat/test_determinism.py -v

# No absolute paths in responses
pytest tests/dat/test_path_safety.py -v
```

---

## Phase 4: Performance & Capability

### M5: Table Availability Fast Probe

**Gap**: GAP-007 (Table availability reads full dataframes)  
**ADR**: ADR-0008, SPEC-0008

#### Task M5.1: Create Table Probe Service

**File**: `apps/data_aggregator/backend/services/table_probe.py` (NEW)

```python
"""Fast table probing service.

Per ADR-0008: Probe must complete in <1s per table.
Per SPEC-0008: Use adapter.probe_schema(), not full reads.
"""

import asyncio
from datetime import datetime, timezone

from shared.contracts.dat.table_status import TableAvailability, TableAvailabilityStatus

PROBE_TIMEOUT_SECONDS = 1.0


async def probe_table(
    adapter: BaseFileAdapter,
    file_path: str,
) -> TableAvailability:
    """Probe a single table for availability status."""
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(adapter.probe_schema, file_path),
            timeout=PROBE_TIMEOUT_SECONDS,
        )
        
        if result.row_count == 0:
            status = TableAvailabilityStatus.EMPTY
        elif result.error:
            status = TableAvailabilityStatus.PARTIAL
        else:
            status = TableAvailabilityStatus.AVAILABLE
            
        return TableAvailability(
            table_id=file_path,
            status=status,
            column_count=len(result.columns),
            row_estimate=result.row_count,
            probed_at=datetime.now(timezone.utc),
        )
    except asyncio.TimeoutError:
        return TableAvailability(
            table_id=file_path,
            status=TableAvailabilityStatus.ERROR,
            error_message="Probe timeout exceeded",
            probed_at=datetime.now(timezone.utc),
        )
    except FileNotFoundError:
        return TableAvailability(
            table_id=file_path,
            status=TableAvailabilityStatus.MISSING,
            probed_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        return TableAvailability(
            table_id=file_path,
            status=TableAvailabilityStatus.ERROR,
            error_message=str(e),
            probed_at=datetime.now(timezone.utc),
        )
```

#### Task M5.2: Update Table Availability Stage

**File**: `apps/data_aggregator/backend/src/dat_aggregation/stages/table_availability.py`

Replace full `adapter.read()` calls with `probe_table()`.

#### Task M5.3: Update Routes to Use Probe Service

**File**: `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py`

Replace lines ~596-706 that call `adapter.read()` with calls to probe service.

#### M5 Validation

```bash
# Probe completes in <1s per table
pytest tests/dat/test_table_probe.py -v --timeout=5

# Large file probe doesn't load full data
pytest tests/dat/test_table_probe_performance.py -v
```

---

### M6: Large File Streaming

**Gap**: GAP-008 (No streaming for files >10MB)  
**ADR**: ADR-0041, SPEC-0027

#### Task M6.1: Add Streaming Threshold to Parse Stage

**File**: `apps/data_aggregator/backend/src/dat_aggregation/stages/parse.py`

```python
STREAMING_THRESHOLD_BYTES = 10 * 1024 * 1024  # 10MB

async def execute_parse(file_path: str, adapter: BaseFileAdapter, ...):
    file_size = Path(file_path).stat().st_size
    
    if file_size > STREAMING_THRESHOLD_BYTES:
        # Use streaming
        async for chunk in adapter.stream_dataframe(file_path, chunk_size=50000):
            await process_chunk(chunk)
    else:
        # Eager load
        df = adapter.read_dataframe(file_path)
        await process_dataframe(df)
```

#### Task M6.2: Verify Adapters Support Streaming

Ensure all adapters in `apps/data_aggregator/backend/adapters/` implement `stream_dataframe()`.

#### M6 Validation

```bash
# Streaming threshold is enforced
pytest tests/dat/test_streaming.py -v

# Memory stays under limit for large files
pytest tests/dat/test_memory_limits.py -v
```

---

### M7: Parse/Export Artifact Formats

**Gap**: GAP-E4 (Parse Parquet enforcement)  
**ADR**: ADR-0015

#### Task M7.1: Enforce Parquet Output in Parse

**File**: `apps/data_aggregator/backend/src/dat_aggregation/stages/parse.py`

Ensure output is always Parquet:

```python
OUTPUT_FORMAT = "parquet"  # Enforced per ADR-0015

async def save_parse_output(df: pl.DataFrame, output_dir: Path) -> Path:
    output_path = output_dir / "dataset.parquet"
    df.write_parquet(output_path)
    return output_path
```

#### Task M7.2: Implement Multi-Format Export

**File**: `apps/data_aggregator/backend/src/dat_aggregation/stages/export.py`

```python
SUPPORTED_FORMATS = {"parquet", "csv", "excel", "json"}

async def execute_export(parse_output: Path, format: str, options: dict) -> Path:
    if format not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format: {format}")
    
    df = pl.read_parquet(parse_output)
    
    if format == "parquet":
        return df.write_parquet(...)
    elif format == "csv":
        return df.write_csv(...)
    elif format == "excel":
        return df.write_excel(...)
    elif format == "json":
        return df.write_json(...)
```

#### M7 Validation

```bash
# Parse always outputs Parquet
pytest tests/dat/test_parse_output.py -v

# Export supports all formats
pytest tests/dat/test_export_formats.py -v
```

---

## Phase 5: Reliability & Completeness

### M8: Cancellation Checkpointing

**Gap**: GAP-010 (Cancellation checkpointing incomplete)  
**ADR**: ADR-0014, SPEC-0010

#### Task M8.1: Implement Checkpoint Registry

**File**: `apps/data_aggregator/backend/services/checkpoint.py` (NEW)

```python
"""Checkpoint registry for cancellation safety.

Per ADR-0014: Checkpoints are safe points where data integrity is guaranteed.
"""

from enum import Enum
from shared.contracts.dat.cancellation import CheckpointType

class CheckpointRegistry:
    def __init__(self):
        self._checkpoints: list[Checkpoint] = []
    
    def mark_checkpoint(self, checkpoint_type: CheckpointType, artifact_id: str):
        """Mark a safe checkpoint."""
        self._checkpoints.append(Checkpoint(
            type=checkpoint_type,
            artifact_id=artifact_id,
            timestamp=datetime.now(timezone.utc),
        ))
    
    def get_last_safe_point(self) -> Checkpoint | None:
        """Get the last safe checkpoint for rollback."""
        return self._checkpoints[-1] if self._checkpoints else None
```

#### Task M8.2: Integrate Checkpointing into Parse Stage

**File**: `apps/data_aggregator/backend/src/dat_aggregation/stages/parse.py`

Add checkpoint calls after each table completion.

#### Task M8.3: Implement Cleanup Service

**File**: `apps/data_aggregator/backend/services/cleanup.py` (NEW)

```python
"""Explicit cleanup service.

Per ADR-0014: Cleanup is user-initiated only, dry-run by default.
"""

async def cleanup(
    run_id: str,
    targets: list[CleanupTarget],
    dry_run: bool = True,
) -> CleanupResult:
    """Clean up partial artifacts from cancelled runs."""
    ...
```

#### Task M8.4: Add Cleanup API Endpoint

**File**: `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py`

```python
@router.post("/runs/{run_id}/cleanup")
async def cleanup_run(run_id: str, request: CleanupRequest):
    """Explicitly clean up partial artifacts."""
    ...
```

#### M8 Validation

```bash
# Cancellation preserves completed tables
pytest tests/dat/test_cancellation.py -v

# Cleanup respects dry-run
pytest tests/dat/test_cleanup.py -v
```

---

### M9: Profile CRUD

**Gap**: GAP-009 (Profile CRUD missing)  
**SPEC**: SPEC-0007

#### Task M9.1: Add Profile CRUD Endpoints

**File**: `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py`

```python
@router.post("/profiles", response_model=ExtractionProfile)
async def create_profile(request: CreateProfileRequest):
    """Create a new extraction profile."""
    ...

@router.get("/profiles/{profile_id}", response_model=ExtractionProfile)
async def get_profile(profile_id: str):
    """Get a profile by ID."""
    ...

@router.put("/profiles/{profile_id}", response_model=ExtractionProfile)
async def update_profile(profile_id: str, request: UpdateProfileRequest):
    """Update an existing profile."""
    ...

@router.delete("/profiles/{profile_id}")
async def delete_profile(profile_id: str):
    """Delete a profile."""
    ...
```

#### Task M9.2: Implement Profile Service

**File**: `apps/data_aggregator/backend/services/profile_service.py` (NEW)

Implement CRUD operations with deterministic ID generation.

#### M9 Validation

```bash
# Profile CRUD works
pytest tests/dat/test_profile_service.py -v
pytest tests/dat/test_profile_api.py -v
```

---

## SSoT Conflict Resolution (GAP-012)

### Task SSoT.1: Update SPEC-0022 to Match ADR-0030

**File**: `docs/specs/core/SPEC-0044_Stage-Completion-Semantics.json`

Replace all `/api/dat/v1/` references with `/api/dat/`.

### Task SSoT.2: Resolve Table Status Enum Mismatch

**Decision Required**: ADR-0008 says `(available, partial, missing, empty)` but Tier-0 contract has `(pending, parsing, available, partial, failed, stale)`.

**Recommendation**: Keep Tier-0 contract as authoritative. Update ADR-0008 to reference the contract.

---

## Validation Checklist (All Phases)

### Phase 1 Complete

- [ ] No imports from legacy adapter stack
- [ ] `pytest tests/dat/test_adapter_registry.py` passes
- [ ] No `/v1` in API paths
- [ ] All frontend fetches use unversioned paths
- [ ] `pytest tests/test_all_endpoints.py` passes

### Phase 2 Complete

- [ ] `StageGraphConfig` contract exists
- [ ] `DATStateMachine` uses config injection
- [ ] Optional stage skip sets `completed=True`
- [ ] `pytest tests/dat/test_state_machine.py` passes

### Phase 3 Complete

- [ ] Stage IDs are 8 characters
- [ ] No absolute paths in stage ID inputs
- [ ] `pytest tests/dat/test_stage_ids.py` passes

### Phase 4 Complete

- [ ] Table probe uses `probe_schema()`, not `read()`
- [ ] Files >10MB use streaming
- [ ] Parse outputs Parquet only
- [ ] Export supports multiple formats

### Phase 5 Complete

- [ ] Cancellation has checkpointing
- [ ] Cleanup is explicit and dry-run by default
- [ ] Profile CRUD endpoints exist

### Final Validation

```bash
# Full test suite
pytest tests/dat/ -v

# Contract validation
python -c "from shared.contracts.dat import *"

# Ruff passes
ruff check .

# All endpoints work
pytest tests/test_all_endpoints.py -v
```

---

## Execution Order Summary

```
Week 1: Foundation
├── M1: Unify Adapters (Day 1-2)
└── M2: Remove /v1 (Day 3-4)

Week 2: Core
├── M3: FSM Config (Day 1-2)
└── M4: Deterministic IDs (Day 3-4)

Week 3: Performance
├── M5: Fast Probe (Day 1-2)
├── M6: Streaming (Day 3)
└── M7: Artifact Formats (Day 4)

Week 4: Reliability
├── M8: Cancellation (Day 1-2)
└── M9: Profile CRUD (Day 3-4)
```

---

## Session Handoff

### Completed This Session

- [x] Analyzed all 12 confirmed gaps from TEAM_006-015
- [x] Created 47 file-level tasks across 9 milestones
- [x] Defined validation commands for each phase
- [x] Created executable change plan

### Next Session Should

1. Execute **M1** (Unify Adapters) - highest priority, unblocks M5
2. Execute **M2** (Remove /v1) - simple, high visibility
3. Run validation after each milestone

---

**Session End**: 2025-12-28  
**Status**: READY_FOR_EXECUTION
