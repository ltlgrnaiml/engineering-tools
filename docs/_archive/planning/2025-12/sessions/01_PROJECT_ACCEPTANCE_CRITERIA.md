# Tier 1: Project-Level Acceptance Criteria

**Purpose**: High-level success criteria that MUST be met for the refactor to be complete.

---

## Global Acceptance Criteria

These criteria apply to ALL milestones:

### AC-GLOBAL-001: Tests Pass

```bash
pytest tests/ -v
# Exit code must be 0
```

### AC-GLOBAL-002: Linting Passes

```bash
ruff check .
# Exit code must be 0
```

### AC-GLOBAL-003: Contract Imports Work

```bash
python -c "from shared.contracts.dat import *"
# No ImportError
```

### AC-GLOBAL-004: No Dead Code

- No commented-out code blocks
- No unused imports
- No orphaned files

### AC-GLOBAL-005: Type Hints Complete

- All public functions have type hints
- No `Any` without justification

---

## Milestone 1: Unify Adapter Implementations

**Gap**: GAP-002 (Two parallel adapter stacks)  
**ADR**: ADR-0011

### AC-M1-001: Legacy Adapters Deleted

The following directory must NOT exist:

```
apps/data_aggregator/backend/src/dat_aggregation/adapters/
```

### AC-M1-002: No Legacy Imports

```bash
grep -r "from.*dat_aggregation.adapters" apps/data_aggregator/backend/src/ --include="*.py"
# Must return empty (no matches)
```

### AC-M1-003: Contract Adapters Used

All adapter usage in routes.py must import from:

```python
from apps.data_aggregator.backend.adapters.registry import AdapterRegistry
```

### AC-M1-004: Adapter Tests Pass

```bash
pytest tests/dat/test_adapter*.py -v
# All tests pass
```

---

## Milestone 2: API Path Normalization

**Gap**: GAP-001 (API uses /v1 prefix)  
**ADR**: ADR-0029

### AC-M2-001: No /v1 in Backend Routes

```bash
grep -r "prefix=\"/v1\"" apps/ gateway/ --include="*.py"
# Must return empty
```

### AC-M2-002: No /v1 in Frontend Fetches

```bash
grep -r "/api/dat/v1" apps/ --include="*.ts" --include="*.tsx" | grep -v node_modules
# Must return empty
```

### AC-M2-003: Gateway Routes Correct

Gateway must mount routers at:

- `/api/datasets` (not `/api/v1/datasets`)
- `/api/pipelines` (not `/api/v1/pipelines`)
- `/api/devtools` (not `/api/v1/devtools`)

### AC-M2-004: Endpoint Tests Pass

```bash
pytest tests/test_all_endpoints.py -v
pytest tests/integration/test_gateway_api.py -v
# All tests pass
```

---

## Milestone 3: Externalize Stage Graph Configuration

**Gap**: GAP-003 (Hardcoded FORWARD_GATES/CASCADE_TARGETS)  
**Gap**: GAP-011 (No Tier-0 StageGraphConfig contract)  
**ADR**: ADR-0001-DAT, ADR-0009

### AC-M3-001: StageGraphConfig Contract Exists

```python
from shared.contracts.dat.stage_graph import StageGraphConfig
# No ImportError
```

### AC-M3-002: Contract Exported in __init__.py

```python
from shared.contracts.dat import StageGraphConfig
# No ImportError
```

### AC-M3-003: FSM Uses Config Injection

`DATStateMachine.__init__` must accept optional `config: StageGraphConfig | None` parameter.

### AC-M3-004: No Hardcoded Gating Rules

`state_machine.py` must NOT have module-level `FORWARD_GATES` or `CASCADE_TARGETS` dicts.

### AC-M3-005: FSM Tests Pass

```bash
pytest tests/dat/test_state_machine.py -v
# All tests pass
```

---

## Milestone 4: Align Stage ID Generation

**Gap**: GAP-005 (Stage ID 16-char vs 8-char)  
**Gap**: GAP-006 (Absolute paths in stage ID inputs)  
**ADR**: ADR-0004-DAT, ADR-0017

### AC-M4-001: Stage IDs Are 8 Characters

```python
from shared.utils.stage_id import compute_stage_id
stage_id = compute_stage_id({"test": "value"})
assert len(stage_id.split("_")[-1]) == 8  # After prefix
```

### AC-M4-002: No Absolute Paths in Inputs

All stage ID computations must use relative paths via `to_relative_path()`.

### AC-M4-003: Path Safety Utility Exists

```python
from shared.contracts.core.path_safety import to_relative_path
# No ImportError
```

### AC-M4-004: Determinism Tests Pass

```bash
pytest tests/dat/test_stage_ids.py -v
pytest tests/dat/test_determinism.py -v
# All tests pass
```

---

## Milestone 5: Table Availability Fast Probe

**Gap**: GAP-007 (Table availability reads full dataframes)  
**ADR**: ADR-0006, SPEC-DAT-0006

### AC-M5-001: Probe Service Exists

```python
from apps.data_aggregator.backend.services.table_probe import probe_table
# No ImportError
```

### AC-M5-002: Uses probe_schema Not read

Routes must call `adapter.probe_schema()`, NOT `adapter.read()`.

### AC-M5-003: Probe Timeout Enforced

Probe must timeout after 1 second per table.

### AC-M5-004: Probe Tests Pass

```bash
pytest tests/dat/test_table_probe.py -v
# All tests pass
```

---

## Milestone 6: Large File Streaming

**Gap**: GAP-008 (No streaming for files >10MB)  
**ADR**: ADR-0040, SPEC-DAT-0004

### AC-M6-001: Streaming Threshold Defined

```python
STREAMING_THRESHOLD_BYTES = 10 * 1024 * 1024  # 10MB
```

### AC-M6-002: Parse Stage Uses Streaming

Files > 10MB must use `adapter.stream_dataframe()`.

### AC-M6-003: All Adapters Support Streaming

All adapters in `apps/data_aggregator/backend/adapters/` must implement `stream_dataframe()`.

### AC-M6-004: Streaming Tests Pass

```bash
pytest tests/dat/test_streaming.py -v
# All tests pass
```

---

## Milestone 7: Parse/Export Artifact Formats

**Gap**: GAP-E4 (Parse Parquet enforcement)  
**ADR**: ADR-0014

### AC-M7-001: Parse Outputs Parquet Only

Parse stage must always output `.parquet` files.

### AC-M7-002: Export Supports Multiple Formats

Export must support: `parquet`, `csv`, `excel`, `json`.

### AC-M7-003: Format Tests Pass

```bash
pytest tests/dat/test_parse_output.py -v
pytest tests/dat/test_export_formats.py -v
# All tests pass
```

---

## Milestone 8: Cancellation Checkpointing

**Gap**: GAP-010 (Cancellation checkpointing incomplete)  
**ADR**: ADR-0013, SPEC-DAT-0015

### AC-M8-001: Checkpoint Registry Exists

```python
from apps.data_aggregator.backend.services.checkpoint import CheckpointRegistry
# No ImportError
```

### AC-M8-002: Cleanup Service Exists

```python
from apps.data_aggregator.backend.services.cleanup import cleanup
# No ImportError
```

### AC-M8-003: Cleanup API Endpoint Exists

```
POST /api/dat/runs/{run_id}/cleanup
```

### AC-M8-004: Cleanup Is Dry-Run by Default

Cleanup must default to `dry_run=True`.

### AC-M8-005: Cancellation Tests Pass

```bash
pytest tests/dat/test_cancellation.py -v
pytest tests/dat/test_cleanup.py -v
# All tests pass
```

---

## Milestone 9: Profile CRUD

**Gap**: GAP-009 (Profile CRUD missing)  
**SPEC**: SPEC-DAT-0005

### AC-M9-001: CRUD Endpoints Exist

```
POST   /api/dat/profiles           # Create
GET    /api/dat/profiles/{id}      # Read
PUT    /api/dat/profiles/{id}      # Update
DELETE /api/dat/profiles/{id}      # Delete
```

### AC-M9-002: Profile Service Exists

```python
from apps.data_aggregator.backend.services.profile_service import ProfileService
# No ImportError
```

### AC-M9-003: Profile IDs Are Deterministic

Profile IDs must be SHA-256 based per ADR-0004.

### AC-M9-004: Profile Tests Pass

```bash
pytest tests/dat/test_profile_service.py -v
pytest tests/dat/test_profile_api.py -v
# All tests pass
```

---

## Verification Matrix

| Milestone | AC Count | Dependencies | Priority |
|-----------|----------|--------------|----------|
| M1 | 4 | None | CRITICAL |
| M2 | 4 | None | CRITICAL |
| M3 | 5 | None | HIGH |
| M4 | 4 | None | HIGH |
| M5 | 4 | M1 | MEDIUM |
| M6 | 4 | None | MEDIUM |
| M7 | 3 | M6 | MEDIUM |
| M8 | 5 | M3 | MEDIUM |
| M9 | 4 | None | LOW |

---

*Next: Read `02_FILE_CHANGE_SPECIFICATIONS.md`*
