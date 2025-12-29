# TEAM_007: DAT Refactor Change Plan

**Session Date**: 2025-12-28
**Status**: PLAN_COMPLETE
**Objective**: Deterministic refactor of DAT subsystem to align with ADRs 0001-0041 and SPECs.
**Driver**: Cascade
**Observer**: User

## 1. SSoT Alignment Matrix

| Component | Current State | SSoT Requirement | Reference |
| :--- | :--- | :--- | :--- |
| **API Routing** | `/api/dat/v1/...` | `/api/dat/...` (Simplified) | ADR-0029 |
| **Stage Graph** | Hardcoded `FORWARD_GATES` | Configurable `StageGraphConfig` | ADR-0001-DAT |
| **Orchestration** | Global Dicts | Instance-based FSM | SPEC-DAT-0001 |
| **Optionality** | Implicit/Unclear | Context/Preview Explicitly Optional | ADR-0003 |
| **Determinism** | Absolute Paths in IDs | Relative/Content-based IDs | ADR-0004-DAT |
| **Table Scan** | Full Read (presumed) | Fast Probe (Headers/Metadata) | ADR-0006 |
| **Adapters** | Split Implementation | Unified Contract Adapters | ADR-0011 |

## 2. Change Plan

### Phase 1: Core Architecture & Routing (Task ID: CORE-*)

- **[CORE-001] API Route Normalization**
  - **Action**: Remove `prefix="/v1"` from `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py`.
  - **Action**: Verify `gateway/main.py` mounts `api/dat` correctly.
  - **Validation**: `GET /api/dat/runs` returns 200 (not 404).

- **[CORE-002] Stage Graph Configuration Injection**
  - **Action**: Refactor `DATStateMachine` to accept `StageGraphConfig` in `__init__`.
  - **Action**: Replace global `FORWARD_GATES` / `CASCADE_TARGETS` with config-driven logic.
  - **Action**: Instantiate `StageGraphConfig` with DAT defaults in `run_manager.py` or factory.
  - **Validation**: Unit test verifying `StageGraphConfig` rules are respected by FSM.

### Phase 2: Determinism & Path Safety (Task ID: SAFE-*)

- **[SAFE-001] Path Normalization in Discovery/Selection**
  - **Action**: Update `Discovery` stage to output relative paths where possible, or clearly scope absolute paths to local environment.
  - **Action**: Update `Selection` stage inputs to use **relative paths** (relative to Discovery root) for ID generation.
  - **Rationale**: `Selection` ID must be reproducible across machines if the same relative file set is selected.
  - **Validation**: `compute_stage_id` for Selection returns same hash for same relative files on different roots.

- **[SAFE-002] Content-Addressed Stage IDs**
  - **Action**: Audit `lock_stage` calls in `routes.py`.
  - **Action**: Ensure `Context`, `TableAvailability`, `TableSelection`, `Preview`, `Parse`, `Export` use strict deterministic inputs (no timestamps, no absolute paths).
  - **Validation**: Verify `stage_id` stability in integration tests.

### Phase 3: Stage Logic Refinement (Task ID: STAGE-*)

- **[STAGE-001] Optional Context & Preview Logic**
  - **Action**: Ensure `Parse` and `Export` do not require `Context` or `Preview` artifacts to exist.
  - **Action**: Implement "Lazy Initialization" for Context defaults if skipped.
  - **Validation**: Run pipeline skipping Context/Preview; Parse/Export succeeds.

- **[STAGE-002] Table Availability Fast Probe**
  - **Action**: Refactor `TableAvailability` execution to use `adapter.probe_schema()` instead of full read.
  - **Action**: Ensure 10MB+ files are handled via streaming check (ADR-0040).
  - **Validation**: `TableAvailability` completes in <1s for 1GB file.

- **[STAGE-003] Unified Adapter Integration**
  - **Action**: Deprecate `src/dat_aggregation/adapters/*`.
  - **Action**: Wire `backend/adapters/*` (Contract-style) into Stage execution logic.
  - **Validation**: Pipeline runs using new adapter registry.

- **[STAGE-004] Cancellation Checkpointing (ADR-0013)**
  - **Action**: Implement "soft cancellation" in `Parse` and `Export` stages.
  - **Action**: Ensure cancellation triggers rollback of partial artifacts (no incomplete Parquet files).
  - **Validation**: Cancelled job leaves no data file, only audit log.

- **[STAGE-005] Artifact Format Enforcement (ADR-0014)**
  - **Action**: Enforce Parquet output for `Parse` stage (no CSV/JSON options at this stage).
  - **Action**: Implement multi-format handlers (Parquet, CSV, JSON) for `Export` stage.
  - **Validation**: Parse always yields `.parquet`; Export yields selected format.

### Phase 4: Validation & Cleanup (Task ID: VAL-*)

- **[VAL-001] Legacy Cleanup**
  - **Action**: Remove unused files in `src/dat_aggregation/adapters`.
  - **Action**: Remove `src/dat_aggregation/core/stage_graph_config.py` if replaced or consolidate.

- **[VAL-002] End-to-End Validation**
  - **Action**: Run `tests/dat/test_e2e_pipeline.py` (to be created/updated).
  - **Validation**: Full Green Pass.

## 3. Acceptance Criteria (Validation Matrix)

### AC-001: API Compliance

- [ ] **Request**: `GET /api/dat/health`
- [ ] **Response**: JSON `{"status": "ok"}`
- [ ] **Requirement**: No `/v1` in path.

### AC-002: Optional Stages

- [ ] **Scenario**: User completes Selection -> Skips Context -> Skips Preview -> Parse.
- [ ] **Result**: Parse succeeds using defaults. Context/Preview stages remain `UNLOCKED` or `SKIPPED` (if we add that state) or just don't block.

### AC-003: Deterministic IDs

- [ ] **Scenario**:
    1. Lock Selection (File A, File B). Get ID `X`.
    2. Unlock Selection.
    3. Lock Selection (File A, File B).
- [ ] **Result**: ID is exactly `X`. Artifact is reused (timestamp unchanged).

### AC-004: Fast Probe

- [ ] **Scenario**: Table Availability on 5GB CSV.
- [ ] **Result**: Returns columns/schema in < 2 seconds. Memory usage < 500MB.

### AC-005: Path Safety

- [ ] **Scenario**: Export Artifact.
- [ ] **Result**: `manifest.json` contains relative paths for `source_files`. `output_path` is relative to workspace root or portable.

## 4. Execution Order

1. **CORE-001** (Routes)
2. **CORE-002** (FSM Config)
3. **SAFE-001** (Path Safety)
4. **STAGE-003** (Adapters) - Prerequisite for optimized probe
5. **STAGE-002** (Fast Probe)
6. **STAGE-001** (Optional Logic)
7. **VAL-001/002** (Cleanup & Test)
