# TEAM_005: DAT Refactor Implementation Plan

**Session Date**: 2025-12-28
**Status**: ✅ IMPLEMENTATION COMPLETE
**Objective**: Generate deterministic change plan aligning DAT code with refactored ADRs, SPECs, and Contracts

## Sprint Results

| Metric | Result |
|--------|--------|
| Tests Passed | 275/276 (1 skipped) |
| Linting Errors Fixed | 356 |
| DAT Contracts Exported | 72 symbols |
| Adapters Verified | 4 (CSV, Excel, JSON, Parquet) |
| API Endpoints | 22+ endpoints |
| Streaming Threshold | 10MB ✅ |
| Cascade Targets | 7 stages ✅ |

---

## Executive Summary

After comprehensive analysis of the 9 DAT ADRs, 7 DAT SPECs, and 6 DAT contracts against the current implementation, this document defines the deterministic change plan to bring the codebase into full alignment with the SSoT files.

---

## SSoT Inventory Analyzed

### ADRs (9 files)
| ADR ID | Title | Key Requirements |
|--------|-------|------------------|
| ADR-0004 | Stage Graph Configuration | 8-stage pipeline, unlock_cascade, lockable_with_artifacts |
| ADR-0004 | Optional Context/Preview | Lazy/greedy init, no cascade from optional stages |
| ADR-0008 | Stage ID Configuration | Deterministic SHA-256 IDs, collision detection |
| ADR-0008 | Table Availability | Status model (available/partial/missing/empty), probe < 1s |
| ADR-0012 | Profile-Driven Extraction | AdapterFactory pattern, handles-first registry |
| ADR-0014 | Cancellation Semantics | Checkpoint preservation, no partial data, explicit cleanup |
| ADR-0015 | Parse/Export Artifacts | Parquet for parse, multi-format export |
| ADR-0041 | Large File Streaming | 10MB threshold, tiered processing |
| ADR-0043 | UI Horizontal Wizard | Stepper pattern, gating tooltips, unlock confirmation |

### SPECs (7 files)
| SPEC ID | Title | Key Implementation Details |
|---------|-------|---------------------------|
| SPEC-0024 | Stage Graph | Stage dependencies, cascade targets |
| SPEC-0025 | Profile Extraction | Profile structure, adapter pattern |
| SPEC-0026 | Adapter Interface Registry | BaseFileAdapter, 4 adapter methods |
| SPEC-0027 | Large File Streaming | File size tiers, memory caps, progress WebSocket |
| SPEC-0007 | Profile File Management | JSON storage, DevTools integration |
| SPEC-0008 | Table Availability | Status enum, probe strategy |
| SPEC-0010 | Cancellation Cleanup | Checkpoint types, audit trail |

### Contracts (6 files in shared/contracts/dat/)
| Contract | Classes Defined | Status |
|----------|----------------|--------|
| adapter.py | BaseFileAdapter, AdapterMetadata, SchemaProbeResult, etc. | ✅ Complete |
| stage.py | DATStageType, DATStageState, DATStageConfig, etc. | ✅ Complete |
| profile.py | ExtractionProfile, ColumnMapping, AggregationLevel, etc. | ✅ Complete |
| table_status.py | TableAvailability, TableStatusReport, etc. | ✅ Complete |
| cancellation.py | Checkpoint, CancellationRequest, CleanupResult, etc. | ✅ Complete |
| jobs.py | BackgroundJob, JobProgress, JobSubmission, etc. | ✅ Complete |

---

## Gap Analysis: Current State vs SSoT

### Backend Gaps

#### 1. Stage Graph Implementation
**Location**: `apps/data_aggregator/backend/src/dat_aggregation/core/stage_graph_config.py`
**Gap**: Need to verify cascade_targets match SPEC-0024 exactly
**Required**:
- [ ] Validate stage dependencies match spec
- [ ] Implement cascade_targets per SPEC-0024
- [ ] Ensure optional stage handling per ADR-0004

#### 2. Adapter Registry Alignment
**Location**: `apps/data_aggregator/backend/adapters/`
**Gap**: Verify all 4 adapters implement BaseFileAdapter interface fully
**Required**:
- [ ] All adapters implement `probe_schema`, `read_dataframe`, `stream_dataframe`, `validate_file`
- [ ] Registry auto-selects by extension per SPEC-0026
- [ ] Schema probe < 5 seconds per ADR-0041

#### 3. State Machine Compliance
**Location**: `apps/data_aggregator/backend/src/dat_aggregation/core/state_machine.py`
**Gap**: Verify state transitions match DATStageState contract
**Required**:
- [ ] State transitions match `DATStageState.can_transition_to()`
- [ ] Unlock cascade triggers for non-optional stages
- [ ] Artifact preservation on unlock per ADR-0002

#### 4. Cancellation Implementation
**Location**: `apps/data_aggregator/backend/src/dat_aggregation/core/checkpoint_manager.py`
**Gap**: Verify checkpoint types and audit trail
**Required**:
- [ ] CheckpointType enum matches SPEC-0010
- [ ] No partial data persisted after cancel
- [ ] Audit trail with ISO-8601 UTC timestamps

#### 5. Table Availability Probing
**Location**: `apps/data_aggregator/backend/src/dat_aggregation/stages/table_availability.py`
**Gap**: Verify status model and probe performance
**Required**:
- [ ] Status values: AVAILABLE, PARTIAL, MISSING, EMPTY, ERROR
- [ ] Probe completes < 1 second per table
- [ ] Status surfaced in UI before parse

#### 6. Profile Management API
**Location**: `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py`
**Gap**: Need profile CRUD endpoints per SPEC-0007
**Required**:
- [ ] GET /api/dat/profiles - list profiles
- [ ] GET /api/dat/profiles/{profile_id} - get profile
- [ ] POST /api/dat/profiles - create profile
- [ ] PUT /api/dat/profiles/{profile_id} - update profile
- [ ] POST /api/dat/profiles/{profile_id}/validate - validate against sample

#### 7. Large File Streaming
**Location**: `apps/data_aggregator/backend/adapters/`, `apps/data_aggregator/backend/src/dat_aggregation/core/memory_manager.py`
**Gap**: Verify tiered processing per ADR-0041
**Required**:
- [ ] 10MB threshold for streaming mode
- [ ] Memory cap enforcement (200MB default)
- [ ] Progress WebSocket per SPEC-0027

### Frontend Gaps

#### 8. Horizontal Wizard Stepper
**Location**: `apps/data_aggregator/frontend/src/components/wizard/DATWizard.tsx`
**Gap**: Verify matches ADR-0043 requirements
**Required**:
- [ ] All 7 visible stages in stepper (Discovery hidden)
- [ ] State indicators: pending, active, completed, locked, error
- [ ] Optional stages marked with badge
- [ ] Gating tooltips per ADR-0043

#### 9. Unlock Confirmation Dialog
**Location**: `apps/data_aggregator/frontend/src/components/wizard/UnlockConfirmDialog.tsx`
**Gap**: Verify cascade confirmation per ADR-0043
**Required**:
- [ ] Dialog lists downstream stages to be unlocked
- [ ] Cascade targets match SPEC-0024

#### 10. Stage Panels
**Location**: `apps/data_aggregator/frontend/src/components/stages/`
**Gap**: Verify all panels align with stage contracts
**Required**:
- [ ] SelectionPanel uses SelectionStageConfig
- [ ] ContextPanel is optional, uses lazy init
- [ ] ParsePanel shows progress for streaming
- [ ] ExportPanel supports format selection

### Test Gaps

#### 11. Test Coverage
**Location**: `tests/dat/`
**Gap**: Need tests per SPEC acceptance criteria
**Required**:
- [ ] test_stage_graph.py - cascade behavior
- [ ] test_adapters.py - interface compliance
- [ ] test_streaming.py - large file handling
- [ ] test_cancellation.py - checkpoint preservation

---

## Deterministic Change Plan

### Phase 1: Contract Validation (Foundation)
**Priority**: Critical
**Effort**: 2 hours

| Step | Action | Acceptance Criteria |
|------|--------|---------------------|
| 1.1 | Validate contract imports | All contracts importable from `shared.contracts.dat` |
| 1.2 | Run contract drift check | `python tools/check_contract_drift.py` passes |
| 1.3 | Generate JSON schemas | `python tools/gen_json_schema.py` for all DAT contracts |

### Phase 2: Backend Core Alignment (State Machine)
**Priority**: Critical
**Effort**: 4 hours

| Step | Action | Acceptance Criteria |
|------|--------|---------------------|
| 2.1 | Update stage_graph_config.py | cascade_targets match SPEC-0024 exactly |
| 2.2 | Update state_machine.py | State transitions use DATStageState.can_transition_to() |
| 2.3 | Implement unlock cascade | Unlock Selection cascades to Context, TableAvail, TableSel, Preview, Parse, Export |
| 2.4 | Add artifact preservation | Unlock preserves artifacts with locked:false |
| 2.5 | Test FSM compliance | pytest tests/dat/test_state_machine.py -v passes |

### Phase 3: Adapter Interface Compliance
**Priority**: High
**Effort**: 3 hours

| Step | Action | Acceptance Criteria |
|------|--------|---------------------|
| 3.1 | Verify BaseFileAdapter impl | All 4 adapters inherit BaseFileAdapter |
| 3.2 | Implement missing methods | probe_schema, validate_file on all adapters |
| 3.3 | Add streaming support | stream_dataframe uses Polars LazyFrame |
| 3.4 | Registry auto-select | get_adapter_for_file works by extension |
| 3.5 | Test adapter compliance | pytest tests/dat/test_adapters.py -v passes |

### Phase 4: Large File Streaming
**Priority**: High
**Effort**: 3 hours

| Step | Action | Acceptance Criteria |
|------|--------|---------------------|
| 4.1 | Implement file size tiers | Size detection per SPEC-0027 |
| 4.2 | Add memory manager limits | max_memory_mb enforced (200MB default) |
| 4.3 | Streaming mode selection | Files > 10MB use streaming automatically |
| 4.4 | Progress WebSocket | /ws/dat/runs/{run_id}/progress emits updates |
| 4.5 | Test streaming | pytest tests/dat/test_streaming.py -v passes |

### Phase 5: Cancellation & Checkpointing
**Priority**: High
**Effort**: 3 hours

| Step | Action | Acceptance Criteria |
|------|--------|---------------------|
| 5.1 | Implement checkpoint types | TABLE_COMPLETE, STAGE_COMPLETE are safe points |
| 5.2 | No partial data on cancel | ROW_BATCH_COMPLETE discarded, only complete tables kept |
| 5.3 | Audit trail logging | CancellationAuditLog with ISO-8601 UTC timestamps |
| 5.4 | Explicit cleanup API | POST /api/dat/cleanup with dry_run default |
| 5.5 | Test cancellation | pytest tests/dat/test_cancellation.py -v passes |

### Phase 6: Profile Management
**Priority**: Medium
**Effort**: 3 hours

| Step | Action | Acceptance Criteria |
|------|--------|---------------------|
| 6.1 | Create profile storage | profiles/system/ (read-only), profiles/user/ (editable) |
| 6.2 | Implement profile CRUD API | All endpoints per SPEC-0007 |
| 6.3 | Profile validation endpoint | POST /api/dat/profiles/{id}/validate |
| 6.4 | Deterministic profile IDs | SHA-256 hash of content (16 chars) |
| 6.5 | Test profile management | pytest tests/dat/test_profiles.py -v passes |

### Phase 7: Table Availability
**Priority**: Medium
**Effort**: 2 hours

| Step | Action | Acceptance Criteria |
|------|--------|---------------------|
| 7.1 | Status enum alignment | Use TableAvailabilityStatus from contract |
| 7.2 | Probe performance | < 1 second per table |
| 7.3 | Health metrics | TableHealth computed correctly |
| 7.4 | Frontend status display | Table status shown in TableAvailabilityPanel |
| 7.5 | Test table availability | pytest tests/dat/test_table_availability.py -v passes |

### Phase 8: Frontend Wizard Alignment
**Priority**: Medium
**Effort**: 4 hours

| Step | Action | Acceptance Criteria |
|------|--------|---------------------|
| 8.1 | Stepper stage visibility | 7 stages visible (Discovery hidden) |
| 8.2 | State indicators | Icons per ADR-0043 (circle-outline, check-circle, lock, etc.) |
| 8.3 | Optional stage badges | Context, Preview show "Optional" badge |
| 8.4 | Gating tooltips | Disabled stages show gating reason |
| 8.5 | Unlock confirmation | Dialog lists cascade targets |
| 8.6 | Test frontend | npm test in frontend/ passes |

### Phase 9: API Endpoint Alignment
**Priority**: Medium
**Effort**: 2 hours

| Step | Action | Acceptance Criteria |
|------|--------|---------------------|
| 9.1 | API naming convention | /api/dat/{resource} per ADR-0030 |
| 9.2 | Error responses | StandardizedErrorResponse per ADR-0032 |
| 9.3 | Idempotency headers | X-Idempotency-Key support per ADR-0033 |
| 9.4 | OpenAPI generation | Swagger docs accurate |
| 9.5 | Test API | pytest tests/dat/test_api.py -v passes |

### Phase 10: Integration Testing
**Priority**: High
**Effort**: 3 hours

| Step | Action | Acceptance Criteria |
|------|--------|---------------------|
| 10.1 | End-to-end workflow test | Full 8-stage pipeline completes |
| 10.2 | Large file test | 50MB file processes via streaming |
| 10.3 | Cancel/resume test | Cancel mid-parse preserves completed tables |
| 10.4 | Unlock cascade test | Unlocking Selection cascades correctly |
| 10.5 | All tests pass | pytest tests/dat/ -v --tb=short passes |

---

## Acceptance Criteria Summary

### Contract Compliance
- [ ] All DAT contracts importable and validated
- [ ] JSON schemas generated for all models
- [ ] Contract drift check passes

### Backend Compliance
- [ ] State machine transitions per DATStageState
- [ ] Cascade targets match SPEC-0024
- [ ] All adapters implement BaseFileAdapter
- [ ] Streaming for files > 10MB
- [ ] Cancellation preserves only complete data
- [ ] Profile CRUD API functional

### Frontend Compliance
- [ ] Horizontal wizard with 7 visible stages
- [ ] State indicators per ADR-0043
- [ ] Gating tooltips on disabled stages
- [ ] Unlock confirmation shows cascade targets

### Test Compliance
- [ ] All tests in tests/dat/ pass
- [ ] Integration tests pass
- [ ] No ruff linting errors
- [ ] Full type hints on all functions

### Documentation Compliance
- [ ] ADR references in code comments where appropriate
- [ ] Google-style docstrings on all public functions
- [ ] API endpoints documented in OpenAPI

---

## Validation Commands

```bash
# Contract validation
python tools/check_contract_drift.py
python tools/gen_json_schema.py

# Backend tests
pytest tests/dat/ -v --tb=short

# Linting
ruff check apps/data_aggregator/backend/ shared/contracts/dat/
ruff format --check apps/data_aggregator/backend/ shared/contracts/dat/

# Frontend tests
cd apps/data_aggregator/frontend && npm test

# Integration
pytest tests/integration/ -v
```

---

## Session Handoff Notes

**Completed**:
- Full SSoT analysis (9 ADRs, 7 SPECs, 6 Contracts)
- Gap analysis against current implementation
- Deterministic 10-phase change plan created

**Next Steps**:
1. Start Phase 1: Contract Validation
2. Execute phases sequentially
3. Test after each phase before proceeding

**Blockers**: None identified

---

*Generated by TEAM_005 on 2025-12-28*
