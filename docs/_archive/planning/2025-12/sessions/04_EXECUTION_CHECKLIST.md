# Tier 4: Step-by-Step Execution Checklist

**Purpose**: Atomic steps for executing each milestone. Follow in order.

---

## Pre-Execution Setup

### SETUP-001: Verify Environment

```bash
# Verify Python environment
python --version  # Must be 3.11+

# Verify dependencies
cd c:/Users/Mycahya/CascadeProjects/engineering-tools
uv sync  # or pip install -e .

# Verify tests pass before starting
pytest tests/ -v --tb=short
```

### SETUP-002: Create Session File

```bash
# Create session tracking file
# Increment from last session number in .sessions/
```

---

## Phase 1: Foundation

---

## Milestone 1: Unify Adapter Implementations

### M1-STEP-001: Verify Contract Adapters Exist

```bash
# Check contract-style adapters exist
ls apps/data_aggregator/backend/adapters/
# Should show: __init__.py, csv_adapter.py, excel_adapter.py, json_adapter.py, parquet_adapter.py, registry.py
```

**CHECKPOINT**: All 6 files exist? YES → Continue. NO → STOP, adapters must exist first.

### M1-STEP-002: Update routes.py Imports

**File**: `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py`

1. Open file
2. Search for `from ..adapters.factory import AdapterFactory`
3. Replace ALL occurrences with:
   ```python
   from apps.data_aggregator.backend.adapters.registry import AdapterRegistry
   ```
4. Save file

### M1-STEP-003: Update routes.py Usage - Pattern 1

**File**: `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py`

1. Search for `AdapterFactory.get_adapter`
2. Replace with `AdapterRegistry.get_adapter`
3. Save file

### M1-STEP-004: Update routes.py Usage - Pattern 2

**File**: `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py`

1. Search for `AdapterFactory.get_tables(Path(`
2. Replace each occurrence:
   ```python
   # OLD
   file_tables = AdapterFactory.get_tables(Path(file_path))
   
   # NEW
   adapter = AdapterRegistry.get_adapter(Path(file_path))
   file_tables = adapter.get_tables(Path(file_path))
   ```
3. Save file

### M1-STEP-005: Update routes.py Usage - Pattern 3

**File**: `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py`

1. Search for `AdapterFactory.get_preview`
2. Replace each occurrence:
   ```python
   # OLD
   preview_df = AdapterFactory.get_preview(Path(file_path), table=table, rows=1)
   
   # NEW
   adapter = AdapterRegistry.get_adapter(Path(file_path))
   preview_df = adapter.read(Path(file_path), table=table).head(1)
   ```
3. Save file

### M1-STEP-006: Delete Legacy Adapter Directory

```bash
# Delete legacy adapters
rm -rf apps/data_aggregator/backend/src/dat_aggregation/adapters/
```

### M1-STEP-007: Verify No Legacy Imports

```bash
# Verify no legacy imports remain
grep -r "from.*dat_aggregation.adapters" apps/data_aggregator/backend/src/ --include="*.py"
# Must return empty
```

**CHECKPOINT**: No results? YES → Continue. NO → Fix remaining imports.

### M1-STEP-008: Run M1 Tests

```bash
pytest tests/dat/test_adapter*.py -v
ruff check apps/data_aggregator/backend/
```

**CHECKPOINT**: All pass? YES → M1 COMPLETE. NO → Debug and fix.

---

## Milestone 2: API Path Normalization

### M2-STEP-001: Update gateway/main.py

**File**: `gateway/main.py`

1. Open file
2. Find lines with `/api/v1/`
3. Replace:
   ```python
   # OLD
   app.include_router(dataset_router, prefix="/api/v1/datasets", tags=["datasets"])
   app.include_router(pipeline_router, prefix="/api/v1/pipelines", tags=["pipelines"])
   app.include_router(devtools_router, prefix="/api/v1/devtools", tags=["devtools"])
   
   # NEW
   app.include_router(dataset_router, prefix="/api/datasets", tags=["datasets"])
   app.include_router(pipeline_router, prefix="/api/pipelines", tags=["pipelines"])
   app.include_router(devtools_router, prefix="/api/devtools", tags=["devtools"])
   ```
4. Save file

### M2-STEP-002: Update gateway/services/pipeline_service.py

**File**: `gateway/services/pipeline_service.py`

1. Open file
2. Find `TOOL_BASE_URLS`
3. Remove `/v1` from all URLs:
   ```python
   TOOL_BASE_URLS = {
       "dat": "http://localhost:8000/api/dat",
       "sov": "http://localhost:8000/api/sov",
       "pptx": "http://localhost:8000/api/pptx",
   }
   ```
4. Save file

### M2-STEP-003: Update DAT routes.py

**File**: `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py`

1. Open file
2. Find line ~39: `router = APIRouter(prefix="/v1")`
3. Replace with: `router = APIRouter()`
4. Update docstring (lines 1-5) to remove `/v1/` reference
5. Save file

### M2-STEP-004: Update SOV routes.py

**File**: `apps/sov_analyzer/backend/src/sov_analyzer/api/routes.py`

1. Open file
2. Find `router = APIRouter(prefix="/v1")`
3. Replace with `router = APIRouter()`
4. Save file

### M2-STEP-005: Update PPTX main.py

**File**: `apps/pptx_generator/backend/main.py`

1. Open file
2. Find all router includes with `/v1/`
3. Remove `/v1/` from all prefixes
4. Save file

### M2-STEP-006: Update DAT Frontend Files

**Files to update** (global find-replace `/api/dat/v1/` → `/api/dat/`):

1. `apps/data_aggregator/frontend/src/hooks/useRun.ts`
2. `apps/data_aggregator/frontend/src/components/stages/SelectionPanel.tsx`
3. `apps/data_aggregator/frontend/src/components/stages/ParsePanel.tsx`
4. `apps/data_aggregator/frontend/src/components/stages/PreviewPanel.tsx`
5. `apps/data_aggregator/frontend/src/components/stages/ContextPanel.tsx`
6. `apps/data_aggregator/frontend/src/components/stages/ExportPanel.tsx`
7. `apps/data_aggregator/frontend/src/components/stages/TableAvailabilityPanel.tsx`
8. `apps/data_aggregator/frontend/src/components/stages/TableSelectionPanel.tsx`

### M2-STEP-007: Update SOV Frontend Files

**File**: `apps/sov_analyzer/frontend/src/components/AnalysisConfig.tsx`

Global find-replace: `/api/sov/v1/` → `/api/sov/`

### M2-STEP-008: Update Homepage Frontend Files

**Files**:
- `apps/homepage/frontend/src/hooks/usePipelines.ts`
- `apps/homepage/frontend/src/hooks/useDataSets.ts`
- `apps/homepage/frontend/src/pages/DataSetDetailsPage.tsx`
- `apps/homepage/frontend/src/pages/PipelineDetailsPage.tsx`
- `apps/homepage/frontend/src/pages/PipelinesPage.tsx`
- `apps/homepage/frontend/src/pages/DevToolsPage.tsx`

Global find-replace: `/api/*/v1/` patterns

### M2-STEP-009: Update Test Files

**Files** (update API paths):
- `tests/dat/test_api.py`
- `tests/test_gateway.py`
- `tests/test_all_endpoints.py`
- `tests/integration/test_gateway_api.py`
- `tests/unit/test_devtools_api.py`
- `test_endpoints_standalone.py`

### M2-STEP-010: Verify No /v1 Remains

```bash
# Backend check
grep -r "prefix=\"/v1\"" apps/ gateway/ --include="*.py"
# Must return empty

# Frontend check
grep -r "/api/dat/v1" apps/ --include="*.ts" --include="*.tsx" | grep -v node_modules
# Must return empty
```

**CHECKPOINT**: Both empty? YES → Continue. NO → Fix remaining occurrences.

### M2-STEP-011: Run M2 Tests

```bash
pytest tests/test_all_endpoints.py -v
pytest tests/integration/test_gateway_api.py -v
ruff check gateway/ apps/
```

**CHECKPOINT**: All pass? YES → M2 COMPLETE. NO → Debug and fix.

---

## Phase 2: FSM Correctness

---

## Milestone 3: Externalize Stage Graph Configuration

### M3-STEP-001: Create stage_graph.py Contract

**File**: `shared/contracts/dat/stage_graph.py`

1. Create new file
2. Copy full code from `03_IMPLEMENTATION_DETAILS.md` section M3-CODE-001
3. Save file

### M3-STEP-002: Verify Contract Import

```bash
python -c "from shared.contracts.dat.stage_graph import StageGraphConfig; print('OK')"
# Must print "OK"
```

**CHECKPOINT**: Prints OK? YES → Continue. NO → Fix import errors.

### M3-STEP-003: Update __init__.py

**File**: `shared/contracts/dat/__init__.py`

1. Add import (after existing imports ~line 67):
   ```python
   from shared.contracts.dat.stage_graph import (
       CascadeRule,
       GatingRule,
       StageDefinition,
       StageGraphConfig,
   )
   ```

2. Add to `__all__` list:
   ```python
       # Stage graph contracts (per ADR-0004)
       "CascadeRule",
       "GatingRule",
       "StageDefinition",
       "StageGraphConfig",
   ```

3. Save file

### M3-STEP-004: Verify Package Export

```bash
python -c "from shared.contracts.dat import StageGraphConfig; print('OK')"
# Must print "OK"
```

### M3-STEP-005: Update state_machine.py - Remove Hardcoded Dicts

**File**: `apps/data_aggregator/backend/src/dat_aggregation/core/state_machine.py`

1. Open file
2. DELETE lines 40-71 (the `FORWARD_GATES` and `CASCADE_TARGETS` dicts)
3. Save file

### M3-STEP-006: Update state_machine.py - Add Config Injection

**File**: `apps/data_aggregator/backend/src/dat_aggregation/core/state_machine.py`

1. Add import at top:
   ```python
   from shared.contracts.dat.stage_graph import StageGraphConfig
   ```

2. Replace `__init__` method with config injection version from `03_IMPLEMENTATION_DETAILS.md` section M3-CODE-003

3. Add `_build_lookup_tables` method

4. Save file

### M3-STEP-007: Update can_lock Method

**File**: `apps/data_aggregator/backend/src/dat_aggregation/core/state_machine.py`

1. Find: `gates = FORWARD_GATES.get(stage, [])`
2. Replace with: `gates = self._forward_gates.get(stage, [])`
3. Save file

### M3-STEP-008: Update unlock_stage Method

**File**: `apps/data_aggregator/backend/src/dat_aggregation/core/state_machine.py`

1. Find: `for target in CASCADE_TARGETS.get(stage, []):`
2. Replace with: `for target in self._cascade_targets.get(stage, []):`
3. Save file

### M3-STEP-009: Delete Orphaned stage_graph_config.py

```bash
# Check if file exists and delete if so
rm -f apps/data_aggregator/backend/src/dat_aggregation/core/stage_graph_config.py
```

### M3-STEP-010: Run M3 Tests

```bash
pytest tests/dat/test_state_machine.py -v
ruff check shared/contracts/dat/ apps/data_aggregator/backend/src/dat_aggregation/core/
```

**CHECKPOINT**: All pass? YES → M3 COMPLETE. NO → Debug and fix.

---

## Phase 3: Determinism

---

## Milestone 4: Align Stage ID Generation

### M4-STEP-001: Update stage_id.py Hash Length

**File**: `shared/utils/stage_id.py`

1. Open file
2. Find: `hash_digest = hashlib.sha256(serialized.encode()).hexdigest()[:16]`
3. Replace with: `hash_digest = hashlib.sha256(serialized.encode()).hexdigest()[:8]`
4. Save file

### M4-STEP-002: Verify path_safety.py Exists

```bash
python -c "from shared.contracts.core.path_safety import to_relative_path; print('OK')"
```

If ImportError, create the function in `shared/contracts/core/path_safety.py`:

```python
def to_relative_path(path: Path, base: Path) -> str:
    """Convert absolute path to relative, raising if not under base."""
    try:
        return str(path.relative_to(base))
    except ValueError:
        raise ValueError(f"Path {path} is not under base {base}")
```

### M4-STEP-003: Update Discovery Inputs in routes.py

**File**: `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py`

1. Find discovery lock endpoint (~line 234)
2. Add import if not present:
   ```python
   from shared.contracts.core.path_safety import to_relative_path
   ```
3. Update inputs:
   ```python
   # OLD
   inputs = {"root_path": str(source_path)}
   
   # NEW
   workspace_root = Path(run.get("workspace", source_path.parent))
   inputs = {"root_path": to_relative_path(source_path, workspace_root)}
   ```
4. Save file

### M4-STEP-004: Run M4 Tests

```bash
pytest tests/dat/test_stage_ids.py -v
pytest tests/dat/test_determinism.py -v
ruff check shared/utils/ apps/data_aggregator/backend/src/dat_aggregation/api/
```

**CHECKPOINT**: All pass? YES → M4 COMPLETE. NO → Debug and fix.

---

## Phase 4: Performance

---

## Milestone 5: Table Availability Fast Probe

### M5-STEP-001: Create services Directory if Needed

```bash
mkdir -p apps/data_aggregator/backend/services
touch apps/data_aggregator/backend/services/__init__.py
```

### M5-STEP-002: Create table_probe.py

**File**: `apps/data_aggregator/backend/services/table_probe.py`

1. Create new file
2. Copy full code from `03_IMPLEMENTATION_DETAILS.md` section M5-CODE-001
3. Save file

### M5-STEP-003: Verify Import

```bash
python -c "from apps.data_aggregator.backend.services.table_probe import probe_table; print('OK')"
```

### M5-STEP-004: Update routes.py Table Availability

**File**: `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py`

1. Add import:
   ```python
   from apps.data_aggregator.backend.services.table_probe import probe_table
   ```

2. Update `scan_table_availability` and `lock_table_availability` endpoints to use `probe_table()` instead of `adapter.read()`

3. Save file

### M5-STEP-005: Run M5 Tests

```bash
pytest tests/dat/test_table_probe.py -v
```

**CHECKPOINT**: All pass? YES → M5 COMPLETE. NO → Debug and fix.

---

## Milestone 6: Large File Streaming

### M6-STEP-001: Add Streaming Threshold to parse.py

**File**: `apps/data_aggregator/backend/src/dat_aggregation/stages/parse.py`

1. Add constant at module level:
   ```python
   STREAMING_THRESHOLD_BYTES = 10 * 1024 * 1024  # 10MB per ADR-0041
   ```
2. Save file

### M6-STEP-002: Update Parse Logic

**File**: `apps/data_aggregator/backend/src/dat_aggregation/stages/parse.py`

1. Update `execute_parse` function to check file size and use streaming for large files
2. Refer to `03_IMPLEMENTATION_DETAILS.md` section M6-CODE-001
3. Save file

### M6-STEP-003: Verify Adapters Support Streaming

```bash
# Check each adapter has stream_dataframe method
grep -l "def stream_dataframe" apps/data_aggregator/backend/adapters/*.py
# Should list all 4 adapter files
```

**CHECKPOINT**: All 4 adapters have method? YES → Continue. NO → Implement missing.

### M6-STEP-004: Run M6 Tests

```bash
pytest tests/dat/test_streaming.py -v
```

**CHECKPOINT**: All pass? YES → M6 COMPLETE. NO → Debug and fix.

---

## Milestone 7: Parse/Export Artifact Formats

### M7-STEP-001: Enforce Parquet in parse.py

**File**: `apps/data_aggregator/backend/src/dat_aggregation/stages/parse.py`

1. Add constant:
   ```python
   OUTPUT_FORMAT = "parquet"  # Enforced per ADR-0015
   ```
2. Update save function to always use Parquet
3. Save file

### M7-STEP-002: Add Multi-Format Export

**File**: `apps/data_aggregator/backend/src/dat_aggregation/stages/export.py`

1. Add supported formats constant
2. Update `execute_export` to support multiple formats
3. Refer to `03_IMPLEMENTATION_DETAILS.md` section M7-CODE-002
4. Save file

### M7-STEP-003: Run M7 Tests

```bash
pytest tests/dat/test_parse_output.py -v
pytest tests/dat/test_export_formats.py -v
```

**CHECKPOINT**: All pass? YES → M7 COMPLETE. NO → Debug and fix.

---

## Phase 5: Reliability

---

## Milestone 8: Cancellation Checkpointing

### M8-STEP-001: Create checkpoint.py

**File**: `apps/data_aggregator/backend/services/checkpoint.py`

1. Create new file
2. Copy full code from `03_IMPLEMENTATION_DETAILS.md` section M8-CODE-001
3. Save file

### M8-STEP-002: Create cleanup.py

**File**: `apps/data_aggregator/backend/services/cleanup.py`

1. Create new file
2. Copy full code from `03_IMPLEMENTATION_DETAILS.md` section M8-CODE-002
3. Save file

### M8-STEP-003: Verify Imports

```bash
python -c "from apps.data_aggregator.backend.services.checkpoint import CheckpointRegistry; print('OK')"
python -c "from apps.data_aggregator.backend.services.cleanup import cleanup; print('OK')"
```

### M8-STEP-004: Add Cleanup Endpoint to routes.py

**File**: `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py`

1. Add import:
   ```python
   from apps.data_aggregator.backend.services.cleanup import cleanup
   from shared.contracts.dat.cancellation import CleanupRequest
   ```

2. Add endpoint:
   ```python
   @router.post("/runs/{run_id}/cleanup")
   async def cleanup_run(run_id: str, request: CleanupRequest):
       """Explicitly clean up partial artifacts."""
       result = await cleanup(
           run_id=run_id,
           targets=request.targets,
           dry_run=request.dry_run,
       )
       return result
   ```

3. Save file

### M8-STEP-005: Run M8 Tests

```bash
pytest tests/dat/test_cancellation.py -v
pytest tests/dat/test_cleanup.py -v
```

**CHECKPOINT**: All pass? YES → M8 COMPLETE. NO → Debug and fix.

---

## Milestone 9: Profile CRUD

### M9-STEP-001: Create profile_service.py

**File**: `apps/data_aggregator/backend/services/profile_service.py`

1. Create new file
2. Copy full code from `03_IMPLEMENTATION_DETAILS.md` section M9-CODE-001
3. Save file

### M9-STEP-002: Verify Import

```bash
python -c "from apps.data_aggregator.backend.services.profile_service import ProfileService; print('OK')"
```

### M9-STEP-003: Add CRUD Endpoints to routes.py

**File**: `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py`

1. Add imports:
   ```python
   from apps.data_aggregator.backend.services.profile_service import ProfileService
   from shared.contracts.dat.profile import CreateProfileRequest, UpdateProfileRequest
   ```

2. Add service instance:
   ```python
   profile_service = ProfileService()
   ```

3. Add all 4 CRUD endpoints from `03_IMPLEMENTATION_DETAILS.md` section M9-CODE-002

4. Save file

### M9-STEP-004: Run M9 Tests

```bash
pytest tests/dat/test_profile_service.py -v
pytest tests/dat/test_profile_api.py -v
```

**CHECKPOINT**: All pass? YES → M9 COMPLETE. NO → Debug and fix.

---

## Final Validation

### FINAL-001: Run Full Test Suite

```bash
pytest tests/ -v
```

### FINAL-002: Run Linting

```bash
ruff check .
```

### FINAL-003: Verify All Contract Imports

```bash
python -c "from shared.contracts.dat import *; print('All contracts OK')"
```

### FINAL-004: Update Session File

Mark all milestones as complete in session file.

---

## Rollback Instructions

If any milestone fails and cannot be fixed:

### Rollback M1

```bash
git checkout -- apps/data_aggregator/backend/src/dat_aggregation/adapters/
git checkout -- apps/data_aggregator/backend/src/dat_aggregation/api/routes.py
```

### Rollback M2

```bash
git checkout -- gateway/
git checkout -- apps/*/backend/src/*/api/routes.py
git checkout -- apps/*/frontend/src/
```

### Rollback M3

```bash
rm shared/contracts/dat/stage_graph.py
git checkout -- shared/contracts/dat/__init__.py
git checkout -- apps/data_aggregator/backend/src/dat_aggregation/core/state_machine.py
```

### Rollback Any Milestone

```bash
git stash
# or
git checkout -- .
```

---

## Completion Checklist

- [ ] M1: Adapter unification complete
- [ ] M2: API path normalization complete
- [ ] M3: Stage graph config externalized
- [ ] M4: Stage ID generation aligned
- [ ] M5: Table probe service created
- [ ] M6: Large file streaming implemented
- [ ] M7: Artifact formats enforced
- [ ] M8: Cancellation checkpointing complete
- [ ] M9: Profile CRUD implemented
- [ ] Final test suite passes
- [ ] Linting passes
- [ ] Session file updated

---

**PATCH PLAN EXECUTION COMPLETE**
