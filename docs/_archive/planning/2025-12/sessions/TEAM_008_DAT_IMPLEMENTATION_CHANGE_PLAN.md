# TEAM_008: DAT Implementation Change Plan

**Session Date**: 2025-12-28
**Status**: IN_PROGRESS
**Objective**: Deterministic implementation of DAT subsystem aligned with 9 ADRs, 7 SPECs, and 7 Tier-0 Contracts
**Predecessor**: TEAM_007_DAT_REFACTOR_PLAN.md
**Driver**: Cascade
**Observer**: Mycahya Eggleston

---

## 1. Executive Summary

This change plan transforms the DAT SSoT (ADRs, SPECs, Contracts) into actionable implementation tasks with concrete acceptance criteria. The contracts in `shared/contracts/dat/` are well-defined and aligned with the ADRs/SPECs. The implementation gap is primarily in `apps/data_aggregator/backend/` where the actual business logic must be built.

### SSoT Inventory (Input Documents)

| Type | Count | Location |
|:-----|:------|:---------|
| DAT ADRs | 9 | `.adrs/dat/` |
| DAT SPECs | 7 | `docs/specs/dat/` |
| DAT Contracts | 7 | `shared/contracts/dat/` |

### Implementation Gap Analysis

| Component | Contract Status | Implementation Status | Gap |
|:----------|:----------------|:----------------------|:----|
| **Stage Contracts** | ✅ Complete (`stage.py`) | ⚠️ Partial (state_machine.py exists) | FSM orchestration logic |
| **Adapter Contracts** | ✅ Complete (`adapter.py`) | ❌ Missing | CSV/Excel/JSON adapters |
| **Profile Contracts** | ✅ Complete (`profile.py`) | ❌ Missing | Profile CRUD + validation |
| **Table Status Contracts** | ✅ Complete (`table_status.py`) | ❌ Missing | Probe + status tracking |
| **Cancellation Contracts** | ✅ Complete (`cancellation.py`) | ❌ Missing | Checkpointing + cleanup |
| **Jobs Contracts** | ✅ Complete (`jobs.py`) | ⚠️ Partial | Job lifecycle service |
| **API Routes** | Contract-defined | ⚠️ Partial | Full CRUD per SPEC |

---

## 2. Implementation Phases

### Phase 0: Foundation Verification [PHASE-0]

Verify the contract layer is complete before implementation.

#### TASK-0.1: Contract Completeness Audit

**Files to verify**:
- `shared/contracts/dat/__init__.py` - Exports all public symbols
- `shared/contracts/dat/stage.py` - All 8 stage configs present
- `shared/contracts/dat/adapter.py` - BaseFileAdapter + registry contracts
- `shared/contracts/dat/profile.py` - ExtractionProfile + CRUD requests
- `shared/contracts/dat/table_status.py` - TableAvailability + StatusReport
- `shared/contracts/dat/cancellation.py` - Checkpoint + cleanup contracts
- `shared/contracts/dat/jobs.py` - DATJob + lifecycle contracts

**Acceptance Criteria**:
- [ ] AC-0.1.1: All contract files have `__version__` attribute
- [ ] AC-0.1.2: All Pydantic models have Google-style docstrings
- [ ] AC-0.1.3: `python -c "from shared.contracts.dat import *"` succeeds
- [ ] AC-0.1.4: `ruff check shared/contracts/dat/` passes

---

### Phase 1: Adapter Layer [PHASE-1]

Implement file adapters per ADR-0012 and SPEC-0026.

#### TASK-1.1: Adapter Registry Implementation

**Location**: `apps/data_aggregator/backend/adapters/registry.py`

**Contract Reference**: `shared.contracts.dat.adapter.AdapterRegistryState`

**Implementation**:
```python
class AdapterRegistry:
    """Central registry for file adapters.
    
    Per ADR-0012: Adapters are selected via handles-first pattern.
    Per SPEC-0026: Registry provides automatic adapter selection.
    """
    
    def register(self, adapter: BaseFileAdapter) -> None: ...
    def get_adapter(self, adapter_id: str) -> BaseFileAdapter: ...
    def get_adapter_for_file(self, file_path: str, mime_type: str | None = None) -> BaseFileAdapter: ...
    def list_adapters(self) -> list[AdapterMetadata]: ...
```

**Acceptance Criteria**:
- [ ] AC-1.1.1: `register()` adds adapter to extension_map for all file_extensions
- [ ] AC-1.1.2: `get_adapter_for_file("test.csv")` returns CSV adapter
- [ ] AC-1.1.3: `AdapterNotFoundError` raised for unknown extensions
- [ ] AC-1.1.4: Registry state serializable to `AdapterRegistryState`

#### TASK-1.2: CSV Adapter Implementation

**Location**: `apps/data_aggregator/backend/adapters/csv_adapter.py`

**Contract Reference**: `shared.contracts.dat.adapter.BaseFileAdapter`

**Implementation Requirements**:
- Implements all 4 abstract methods: `probe_schema`, `read_dataframe`, `stream_dataframe`, `validate_file`
- Uses Polars `read_csv` for eager loading, `scan_csv` for streaming
- Supports `.csv` and `.tsv` extensions
- Streaming threshold: 10MB (per ADR-0041)

**Acceptance Criteria**:
- [ ] AC-1.2.1: `probe_schema()` returns `SchemaProbeResult` with columns, row estimate
- [ ] AC-1.2.2: `probe_schema()` completes in < 5 seconds for 1GB file
- [ ] AC-1.2.3: `read_dataframe()` returns `(pl.DataFrame, ReadResult)` tuple
- [ ] AC-1.2.4: `stream_dataframe()` yields chunks with `StreamChunk` metadata
- [ ] AC-1.2.5: `validate_file()` returns `FileValidationResult`
- [ ] AC-1.2.6: Delimiter detection works for comma, tab, semicolon

#### TASK-1.3: Excel Adapter Implementation

**Location**: `apps/data_aggregator/backend/adapters/excel_adapter.py`

**Implementation Requirements**:
- Supports `.xlsx` and `.xls` extensions
- Uses Polars `read_excel` (no streaming for Excel)
- Multi-sheet support via `SheetInfo`
- Max recommended size: 100MB

**Acceptance Criteria**:
- [ ] AC-1.3.1: `probe_schema()` returns sheet list for multi-sheet files
- [ ] AC-1.3.2: Sheet selection via `ReadOptions.extra["sheet_name"]`
- [ ] AC-1.3.3: `capabilities.supports_streaming` is `False`
- [ ] AC-1.3.4: `capabilities.supports_multiple_sheets` is `True`

#### TASK-1.4: JSON Adapter Implementation

**Location**: `apps/data_aggregator/backend/adapters/json_adapter.py`

**Implementation Requirements**:
- Supports `.json`, `.jsonl`, `.ndjson` extensions
- Uses Polars `read_json` for regular JSON, `read_ndjson` for line-delimited
- Streaming via `scan_ndjson` for JSONL files > 10MB

**Acceptance Criteria**:
- [ ] AC-1.4.1: Auto-detects JSON vs JSONL format
- [ ] AC-1.4.2: Streaming works for `.ndjson` files > 10MB
- [ ] AC-1.4.3: Nested JSON flattened or handled per schema

---

### Phase 2: FSM Orchestration [PHASE-2]

Implement stage state machine per ADR-0004 and SPEC-0024.

#### TASK-2.1: Stage Graph Configuration

**Location**: `apps/data_aggregator/backend/core/stage_graph.py`

**Contract Reference**: `shared.contracts.dat.stage.DATStageType`

**Implementation**:
```python
@dataclass
class StageGraphConfig:
    """DAT 8-stage pipeline configuration.
    
    Per ADR-0004: 8 stages with lockable artifacts.
    Per SPEC-0024: Dependencies and cascade targets defined.
    """
    
    stages: list[StageDefinition]
    dependencies: dict[DATStageType, list[DATStageType]]
    cascade_targets: dict[DATStageType, list[DATStageType]]
    optional_stages: set[DATStageType]
```

**Acceptance Criteria**:
- [ ] AC-2.1.1: All 8 stages defined: DISCOVERY, SELECTION, CONTEXT, TABLE_AVAILABILITY, TABLE_SELECTION, PREVIEW, PARSE, EXPORT
- [ ] AC-2.1.2: Dependencies match SPEC-0024 `stage_dependencies`
- [ ] AC-2.1.3: Cascade targets match SPEC-0024 `cascade_targets`
- [ ] AC-2.1.4: Optional stages = {CONTEXT, PREVIEW} per ADR-0004

#### TASK-2.2: DAT State Machine Refactor

**Location**: `apps/data_aggregator/backend/core/state_machine.py`

**Contract Reference**: `shared.contracts.dat.stage.DATStageState`

**Implementation Requirements**:
- Accept `StageGraphConfig` in constructor (not global dicts)
- Implement forward gating per ADR-0004
- Implement unlock cascade per ADR-0004
- Preserve artifacts on unlock per ADR-0002

**Key Methods**:
```python
class DATStateMachine:
    def can_lock(self, stage: DATStageType) -> tuple[bool, str | None]: ...
    def lock_stage(self, stage: DATStageType, inputs: dict) -> DATStageResult: ...
    def unlock_stage(self, stage: DATStageType) -> list[DATStageType]: ...  # Returns cascaded unlocks
    def can_progress_to(self, stage: DATStageType) -> bool: ...
```

**Acceptance Criteria**:
- [ ] AC-2.2.1: `can_lock(PARSE)` returns `(True, None)` when TABLE_SELECTION is locked
- [ ] AC-2.2.2: `can_lock(EXPORT)` returns `(False, "PARSE not locked")` when PARSE unlocked
- [ ] AC-2.2.3: `unlock_stage(SELECTION)` cascades unlock to 6 downstream stages
- [ ] AC-2.2.4: Optional stage skip: `can_lock(TABLE_AVAILABILITY)` succeeds even if CONTEXT not locked
- [ ] AC-2.2.5: State transitions follow `DATStageState.can_transition_to()`

#### TASK-2.3: Deterministic Stage ID Generation

**Location**: `apps/data_aggregator/backend/core/id_generator.py`

**Contract Reference**: `shared.contracts.core.id_generator.compute_deterministic_id`

**Implementation Requirements**:
- Stage ID = SHA-256 hash of sorted, normalized inputs
- Inputs must use relative paths (not absolute)
- Same inputs → Same ID across machines
- Collision detection before artifact reuse

**Per-Stage ID Inputs** (per ADR-0008):
| Stage | ID Inputs |
|:------|:----------|
| SELECTION | `[sorted(relative_file_paths), profile_id]` |
| CONTEXT | `[selection_id, sorted(context_hints)]` |
| TABLE_AVAILABILITY | `[selection_id, profile_id, probe_options]` |
| TABLE_SELECTION | `[table_availability_id, sorted(selected_tables)]` |
| PREVIEW | `[table_selection_id, preview_options]` |
| PARSE | `[table_selection_id, profile_id, parse_options]` |
| EXPORT | `[parse_id, export_formats, output_path]` |

**Acceptance Criteria**:
- [ ] AC-2.3.1: `compute_stage_id(inputs, seed=42)` is deterministic
- [ ] AC-2.3.2: Same files selected on different machines → Same ID
- [ ] AC-2.3.3: ID prefix is 8 characters (default)
- [ ] AC-2.3.4: Collision detected if ID exists with different input hash

---

### Phase 3: Table Availability [PHASE-3]

Implement table probing per ADR-0008 and SPEC-0008.

#### TASK-3.1: Table Probe Service

**Location**: `apps/data_aggregator/backend/services/table_probe.py`

**Contract Reference**: `shared.contracts.dat.table_status.TableAvailability`

**Implementation Requirements**:
- Use adapter's `probe_schema()` for fast probing
- Status model: AVAILABLE, PARTIAL, MISSING, EMPTY, ERROR
- Timeout: 1 second per table (per ADR-0008)
- Parallel probing for multiple files

**Acceptance Criteria**:
- [ ] AC-3.1.1: Probe 100 CSV files in < 10 seconds (parallel)
- [ ] AC-3.1.2: Large file (1GB) probe completes in < 5 seconds
- [ ] AC-3.1.3: Missing file returns status=MISSING
- [ ] AC-3.1.4: Empty file (headers only) returns status=EMPTY
- [ ] AC-3.1.5: Corrupted file returns status=ERROR with message

#### TASK-3.2: Table Status Report API

**Location**: `apps/data_aggregator/backend/api/routes/tables.py`

**Endpoint**: `GET /api/dat/runs/{run_id}/stages/table_availability/tables`

**Response Contract**: `TableStatusReport`

**Acceptance Criteria**:
- [ ] AC-3.2.1: Returns list of `TableAvailabilityRef` items
- [ ] AC-3.2.2: Includes summary stats (total, available, partial, failed)
- [ ] AC-3.2.3: Response matches `TableStatusReport` schema exactly

---

### Phase 4: Profile Management [PHASE-4]

Implement profile CRUD per ADR-0012 and SPEC-0007.

#### TASK-4.1: Profile File Service

**Location**: `apps/data_aggregator/backend/services/profile_service.py`

**Contract Reference**: `shared.contracts.dat.profile.ExtractionProfile`

**Implementation Requirements**:
- Profiles stored as JSON in `apps/data_aggregator/config/profiles/`
- System profiles in `profiles/system/` (read-only)
- User profiles in `profiles/user/` (editable)
- Profile ID = SHA-256 hash of content (first 16 chars)

**Acceptance Criteria**:
- [ ] AC-4.1.1: `list_profiles()` returns `list[ExtractionProfileRef]`
- [ ] AC-4.1.2: `get_profile(id)` returns `ExtractionProfile`
- [ ] AC-4.1.3: `create_profile(request)` generates deterministic ID
- [ ] AC-4.1.4: `update_profile(id, request)` bumps version
- [ ] AC-4.1.5: System profiles raise `PermissionError` on update/delete

#### TASK-4.2: Profile Validation Service

**Location**: `apps/data_aggregator/backend/services/profile_validator.py`

**Contract Reference**: `shared.contracts.dat.profile.ProfileValidationResult`

**Implementation Requirements**:
- JSON schema validation
- Pydantic model validation
- Cross-reference validation (column mappings)
- Sample file preview

**Acceptance Criteria**:
- [ ] AC-4.2.1: Invalid JSON returns errors with line numbers
- [ ] AC-4.2.2: Missing required field returns error
- [ ] AC-4.2.3: `validate_against_sample(profile, file)` returns matched columns

---

### Phase 5: Parse & Export Stages [PHASE-5]

Implement core data processing per ADR-0015.

#### TASK-5.1: Parse Stage Implementation

**Location**: `apps/data_aggregator/backend/stages/parse.py`

**Contract Reference**: `shared.contracts.dat.stage.ParseStageConfig`

**Implementation Requirements**:
- Output format: Parquet only (per ADR-0015)
- Use adapter streaming for files > 10MB
- Generate manifest.json with provenance
- Support cancellation with checkpointing

**Output Bundle**:
```
{run_id}/stages/parse/
├── dataset.parquet
├── manifest.json
├── prep_report.json
└── transform_plan.json
```

**Acceptance Criteria**:
- [ ] AC-5.1.1: Parse output is always Parquet
- [ ] AC-5.1.2: manifest.json includes `source_files`, `profile_id`, `row_count`
- [ ] AC-5.1.3: Large file (100MB) uses streaming
- [ ] AC-5.1.4: Progress updates emitted every 5 seconds
- [ ] AC-5.1.5: Cancellation preserves completed tables only

#### TASK-5.2: Export Stage Implementation

**Location**: `apps/data_aggregator/backend/stages/export.py`

**Contract Reference**: `shared.contracts.dat.stage.ExportStageConfig`

**Implementation Requirements**:
- Requires PARSE locked and completed
- User-selectable formats: Parquet, CSV, Excel, JSON
- Reads from Parse stage Parquet
- Generates format-specific output

**Acceptance Criteria**:
- [ ] AC-5.2.1: Export blocked if Parse not locked
- [ ] AC-5.2.2: CSV export with configurable delimiter
- [ ] AC-5.2.3: Excel export with sheet naming
- [ ] AC-5.2.4: JSON export with configurable indent

---

### Phase 6: Cancellation & Cleanup [PHASE-6]

Implement cancellation per ADR-0014 and SPEC-0010.

#### TASK-6.1: Cancellation Handler

**Location**: `apps/data_aggregator/backend/services/cancellation.py`

**Contract Reference**: `shared.contracts.dat.cancellation.*`

**Implementation Requirements**:
- Soft cancellation: preserve completed artifacts
- Checkpointing: TABLE_COMPLETE and STAGE_COMPLETE are safe points
- No partial data persisted (rollback incomplete)
- Audit trail for all cancellation events

**Acceptance Criteria**:
- [ ] AC-6.1.1: Cancel during Parse preserves completed tables
- [ ] AC-6.1.2: Cancel during row batch discards partial batch
- [ ] AC-6.1.3: `CancellationAuditLog` contains all events
- [ ] AC-6.1.4: Timestamps are ISO-8601 UTC (no microseconds)

#### TASK-6.2: Cleanup Service

**Location**: `apps/data_aggregator/backend/services/cleanup.py`

**Contract Reference**: `shared.contracts.dat.cancellation.CleanupRequest`

**Implementation Requirements**:
- Explicit user-initiated cleanup only
- Dry run by default
- Targets: temp_files, partial_artifacts, orphaned_checkpoints
- Returns bytes freed

**Acceptance Criteria**:
- [ ] AC-6.2.1: `dry_run=True` reports items without deleting
- [ ] AC-6.2.2: Cleanup never deletes completed artifacts
- [ ] AC-6.2.3: `CleanupResult` includes `bytes_freed`

---

### Phase 7: API Routes [PHASE-7]

Complete API implementation per ADR-0030.

#### TASK-7.1: DAT API Routes

**Location**: `apps/data_aggregator/backend/api/routes/`

**Base Path**: `/api/dat/`

**Required Endpoints**:

| Method | Path | Description | Request | Response |
|:-------|:-----|:------------|:--------|:---------|
| GET | `/health` | Health check | - | `{"status": "ok"}` |
| GET | `/adapters` | List adapters | - | `list[AdapterMetadata]` |
| GET | `/profiles` | List profiles | - | `list[ExtractionProfileRef]` |
| POST | `/profiles` | Create profile | `CreateProfileRequest` | `ExtractionProfile` |
| GET | `/profiles/{id}` | Get profile | - | `ExtractionProfile` |
| PUT | `/profiles/{id}` | Update profile | `UpdateProfileRequest` | `ExtractionProfile` |
| DELETE | `/profiles/{id}` | Delete profile | - | 204 |
| GET | `/runs` | List runs | - | `list[DATJobRef]` |
| POST | `/runs` | Create run | `CreateJobRequest` | `DATJob` |
| GET | `/runs/{id}` | Get run | - | `DATJob` |
| DELETE | `/runs/{id}` | Delete run | - | 204 |
| GET | `/runs/{id}/stages` | List stages | - | `list[DATStageRef]` |
| POST | `/runs/{id}/stages/{stage}/lock` | Lock stage | `LockStageRequest` | `DATStageResult` |
| POST | `/runs/{id}/stages/{stage}/unlock` | Unlock stage | - | `UnlockResult` |
| POST | `/runs/{id}/cancel` | Cancel run | `CancellationRequest` | `CancellationResult` |

**Acceptance Criteria**:
- [ ] AC-7.1.1: All endpoints return Pydantic-validated responses
- [ ] AC-7.1.2: Error responses follow `StandardizedErrorResponse` schema
- [ ] AC-7.1.3: No `/v1` in any path (per ADR-0030)
- [ ] AC-7.1.4: Idempotency keys supported on POST/PUT (per ADR-0033)

---

## 3. Validation Commands

```bash
# Phase 0: Contract validation
python -c "from shared.contracts.dat import *"
ruff check shared/contracts/dat/
pytest tests/test_contracts.py -v -k dat

# Phase 1: Adapter tests
pytest tests/dat/test_adapters.py -v
pytest tests/dat/test_adapter_registry.py -v

# Phase 2: FSM tests
pytest tests/dat/test_state_machine.py -v
pytest tests/dat/test_stage_ids.py -v

# Phase 3: Table probe tests
pytest tests/dat/test_table_probe.py -v

# Phase 4: Profile tests
pytest tests/dat/test_profile_service.py -v
pytest tests/dat/test_profile_validation.py -v

# Phase 5: Parse/Export tests
pytest tests/dat/test_parse_stage.py -v
pytest tests/dat/test_export_stage.py -v

# Phase 6: Cancellation tests
pytest tests/dat/test_cancellation.py -v
pytest tests/dat/test_cleanup.py -v

# Phase 7: API tests
pytest tests/dat/test_api_routes.py -v

# Integration tests
pytest tests/integration/test_dat_pipeline.py -v

# Full DAT test suite
pytest tests/dat/ -v --tb=short
```

---

## 4. Execution Order & Dependencies

```
Phase 0 (Contracts) → Phase 1 (Adapters) → Phase 2 (FSM)
                                              ↓
                       Phase 3 (Table Probe) ← 
                                              ↓
                       Phase 4 (Profiles)    → Phase 5 (Parse/Export)
                                              ↓
                       Phase 6 (Cancellation) → Phase 7 (API Routes)
```

### Critical Path

1. **TASK-1.1** (Adapter Registry) - Foundation for all file operations
2. **TASK-1.2** (CSV Adapter) - Most common format, enables testing
3. **TASK-2.2** (State Machine) - Core orchestration logic
4. **TASK-2.3** (Stage IDs) - Determinism guarantee
5. **TASK-5.1** (Parse Stage) - Primary data processing
6. **TASK-7.1** (API Routes) - External interface

---

## 5. Acceptance Criteria Summary

### Code Quality Gates

- [ ] **CQ-001**: All Python files pass `ruff check`
- [ ] **CQ-002**: All Python files pass `ruff format --check`
- [ ] **CQ-003**: All public functions have Google-style docstrings
- [ ] **CQ-004**: All functions have type hints
- [ ] **CQ-005**: Test coverage > 80% for new code

### Contract Compliance Gates

- [ ] **CC-001**: All API responses match Pydantic contract schemas
- [ ] **CC-002**: All stage configs match `DATStageConfig` union
- [ ] **CC-003**: All adapters implement `BaseFileAdapter` interface
- [ ] **CC-004**: All profiles validate against `ExtractionProfile` schema

### ADR Compliance Gates

- [ ] **ADR-0004**: 8-stage FSM with lockable artifacts
- [ ] **ADR-0004**: Context/Preview are optional
- [ ] **ADR-0008**: Deterministic stage IDs
- [ ] **ADR-0008**: Fast table probe (< 1 second per table)
- [ ] **ADR-0012**: Profile-driven adapters
- [ ] **ADR-0014**: Soft cancellation with checkpointing
- [ ] **ADR-0015**: Parquet for Parse, multi-format for Export
- [ ] **ADR-0041**: Streaming for files > 10MB
- [ ] **ADR-0043**: Horizontal wizard UI (frontend)

---

## 6. Session Handoff Notes

### Completed This Session
- [x] SSoT analysis of 9 DAT ADRs
- [x] SSoT analysis of 7 DAT SPECs
- [x] Gap analysis of 7 DAT contracts
- [x] Generated comprehensive change plan with 7 phases, 18 tasks
- [x] Defined 60+ acceptance criteria

### Remaining Work
- [ ] Implement Phase 1-7 tasks
- [ ] Create test fixtures for adapters
- [ ] Implement frontend horizontal wizard (ADR-0043)
- [ ] DevTools profile editor integration (SPEC-0007)

### Next Session Should
1. Start with TASK-1.1 (Adapter Registry)
2. Implement TASK-1.2 (CSV Adapter) for initial testing
3. Build TASK-2.2 (State Machine) for orchestration
4. Run validation commands after each phase

---

**Session End**: 2025-12-28
**Next Session**: TEAM_009 (Implementation Phase 1)
